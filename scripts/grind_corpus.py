#!/usr/bin/env python3
"""Hearth corpus grind v2 — a PERPETUAL data engine.

Keeps pulling more and more training data, unattended, until a disk cap is hit.
Three sources of breadth:
  1. A big curated list of known-good datasets per family.
  2. DISCOVERY: query the HF Hub for every family keyword and pull the top reachable
     datasets we don't already have — so coverage keeps widening on its own.
  3. A LOOP: repeat with different sort orders (downloads / trending / recent) so each
     cycle surfaces datasets the last one didn't.

Idempotent: any output file that exists is skipped, so re-runs only add NEW data.
Legal posture (settled): fair-use training inputs; record provenance; never
redistributed (stays out of the repo). See docs/corpus-sourcing.md.
"""
import os, sys, json, csv, time, fcntl

ROOT = os.path.expanduser("~/Downloads/hearth-corpus")
MAN  = os.path.join(ROOT, "_manifests", "manifest.csv")
LOG  = os.path.join(ROOT, "_logs", "grind.log")
FAM_DIR = {"A": "A-imagination", "B": "B-utility", "C": "C-companion", "D": "D-buildyourown"}
for d in list(FAM_DIR.values()) + ["_manifests", "_logs"]:
    os.makedirs(os.path.join(ROOT, d), exist_ok=True)
if not os.path.exists(MAN):
    open(MAN, "w").write("family,filename,title,source_url,license,words,retrieved,notes\n")

TODAY = "2026-06-02"
DISK_CAP_GB = float(os.environ.get("HEARTH_DISK_CAP_GB", "60"))
PER_DATASET_CAP = int(os.environ.get("HEARTH_PER_CAP", "120000"))
MAX_CYCLES = int(os.environ.get("HEARTH_CYCLES", "8"))
MAX_DS_BYTES = int(os.environ.get("HEARTH_MAX_DS_MB", "300")) * 1_000_000  # cap any one dataset
MIN_PROSE_WORDS = 12  # skip non-text datasets (EEG/crystal/audio matched by keyword)


def clean_hf_cache():
    """Delete the HuggingFace download cache — it keeps raw copies on top of our jsonl
    and was the disk-killer. Our jsonl is the keeper; the cache is disposable."""
    import shutil
    for p in ("~/.cache/huggingface/hub", "~/.cache/huggingface/datasets"):
        shutil.rmtree(os.path.expanduser(p), ignore_errors=True)


def looks_like_prose(rec):
    """True if the record's biggest text field reads like prose (filters non-text junk)."""
    t = rec if isinstance(rec, str) else (
        max((v for v in rec.values() if isinstance(v, str)), key=len, default="")
        if isinstance(rec, dict) else "")
    return len(t.split()) >= MIN_PROSE_WORDS and " " in t.strip()

def log(m):
    line = f"[{time.strftime('%m-%d %H:%M:%S')}] {m}"
    print(line, flush=True)
    with open(LOG, "a") as f: f.write(line + "\n")

def manifest(row):
    with open(MAN, "a", newline="") as f:
        fcntl.flock(f, fcntl.LOCK_EX); csv.writer(f).writerow(row); fcntl.flock(f, fcntl.LOCK_UN)

def corpus_bytes():
    return sum(os.path.getsize(os.path.join(dp, f))
               for fam in FAM_DIR.values()
               for dp, _, fs in os.walk(os.path.join(ROOT, fam)) for f in fs)

def words_of(ex):
    if isinstance(ex, str): return len(ex.split())
    if isinstance(ex, dict):
        tot = 0
        for v in ex.values():
            if isinstance(v, str): tot += len(v.split())
            elif isinstance(v, list):
                for it in v:
                    if isinstance(it, str): tot += len(it.split())
                    elif isinstance(it, dict): tot += sum(len(str(x).split()) for x in it.values() if isinstance(x, str))
        return tot
    return 0

def have(fam, hf_id):
    return os.path.exists(os.path.join(ROOT, FAM_DIR[fam], hf_id.replace("/", "__") + ".jsonl"))

def _salvage(fam, hf_id, out, cap):
    """When load_dataset fails (deprecated loader script, odd schema), pull the raw
    data files directly and read them. Recovers a lot of otherwise-dropped data."""
    from huggingface_hub import HfApi, hf_hub_download
    api = HfApi()
    try:
        files = api.list_repo_files(hf_id, repo_type="dataset")
    except Exception:
        return 0
    data_files = [f for f in files if f.lower().endswith((".parquet", ".jsonl", ".json", ".csv"))
                  and "test" not in f.lower() and "valid" not in f.lower()]
    data_files = sorted(data_files)[:3]  # bounded
    if not data_files:
        return 0
    n = wc = nbytes = 0
    tmp = out + ".part"
    try:
        with open(tmp, "w") as fout:
            for df in data_files:
                if n >= cap or nbytes >= MAX_DS_BYTES: break
                try:
                    local = hf_hub_download(hf_id, df, repo_type="dataset")
                except Exception:
                    continue
                rows = []
                if df.endswith(".parquet"):
                    import pyarrow.parquet as pq
                    rows = pq.read_table(local).to_pylist()
                elif df.endswith((".jsonl", ".json")):
                    txt = open(local, encoding="utf-8", errors="ignore").read().strip()
                    try:
                        rows = json.loads(txt); rows = rows if isinstance(rows, list) else [rows]
                    except Exception:
                        rows = [json.loads(l) for l in txt.splitlines() if l.strip()]
                elif df.endswith(".csv"):
                    import csv as _csv
                    rows = list(_csv.DictReader(open(local, encoding="utf-8", errors="ignore")))
                if rows and not looks_like_prose(rows[0]):
                    break  # non-text dataset — skip
                for r in rows:
                    if n >= cap or nbytes >= MAX_DS_BYTES: break
                    line = json.dumps(r, ensure_ascii=False) + "\n"
                    fout.write(line); n += 1; nbytes += len(line); wc += words_of(r)
        if n == 0:
            os.remove(tmp); return 0
        os.replace(tmp, out)
        manifest([fam, os.path.basename(out), hf_id.split("/")[-1],
                  f"https://huggingface.co/datasets/{hf_id}", "fair-use-training-input",
                  wc, TODAY, f"{n} ex; SALVAGED via direct file download"])
        log(f"OK(salvage) [{fam}] {hf_id}: {n} ex ~{wc//1000}k words")
        return wc
    except Exception as e:
        if os.path.exists(tmp):
            try: os.remove(tmp)
            except OSError: pass
        return 0


def grab(fam, hf_id, cap=PER_DATASET_CAP, note="", config=None):
    if have(fam, hf_id):
        return 0
    out = os.path.join(ROOT, FAM_DIR[fam], hf_id.replace("/", "__") + ".jsonl")
    tmp = out + ".part"
    try:
        from datasets import load_dataset
        n = wc = 0
        try:
            ds = load_dataset(hf_id, config, split="train", streaming=True) if config \
                 else load_dataset(hf_id, split="train", streaming=True)
        except Exception:
            d = load_dataset(hf_id, config) if config else load_dataset(hf_id)
            ds = d["train" if "train" in d else list(d.keys())[0]]
        nbytes = 0; checked = False
        with open(tmp, "w") as f:
            for ex in ds:
                if n >= cap or nbytes >= MAX_DS_BYTES: break
                if not checked:  # prose-gate on the first example; skip non-text datasets
                    checked = True
                    if not looks_like_prose(ex):
                        break
                line = json.dumps(ex, ensure_ascii=False) + "\n"
                f.write(line); n += 1; nbytes += len(line); wc += words_of(ex)
        if n == 0:
            os.remove(tmp); clean_hf_cache(); return 0
        os.replace(tmp, out)
        clean_hf_cache()  # critical: drop the raw download cache so disk doesn't bloat
        manifest([fam, os.path.basename(out), hf_id.split("/")[-1],
                  f"https://huggingface.co/datasets/{hf_id}", "fair-use-training-input",
                  wc, TODAY, f"{n} ex; {note}"])
        log(f"OK [{fam}] {hf_id}: {n} ex ~{wc//1000}k words")
        return wc
    except Exception as e:
        if os.path.exists(tmp):
            try: os.remove(tmp)
            except OSError: pass
        # loader failed — try pulling the raw files directly before giving up
        saved = _salvage(fam, hf_id, out, cap)
        clean_hf_cache()
        if saved == 0:
            log(f"FAIL [{fam}] {hf_id}: {str(e)[:110]}")
        return saved

# ------------------------------------------------------- curated seed list
SEED = [
  # A — imagination / meditation / vivid-sensory prose
  ("A","carecodeconnect/jhana-guided-meditations-collection",""),
  ("A","theprint/mindfulness-alpaca",""),
  ("A","euclaise/writingprompts","creative prose for vivid voice"),
  ("A","Gryphe/Opus-WritingPrompts","creative writing"),
  ("A","nRuaif/creative_writing","creative writing"),
  # B — utility
  ("B","HuggingFaceH4/no_robots",""),("B","databricks/databricks-dolly-15k",""),
  ("B","knkarthick/dialogsum",""),("B","Yale-LILY/aeslc",""),("B","knkarthick/samsum",""),
  ("B","EdinburghNLP/xsum","news summarization"),("B","cnn_dailymail","summarization"),
  ("B","gigaword","headline summarization"),("B","wiki_lingua","how-to summarization"),
  # C — companion (honest + SMART/generative, not prescriptive)
  ("C","to-be/annomi-motivational-interviewing-therapy-conversations","GOLD honest-mirror"),
  ("C","nbertagnolli/counsel-chat","therapist Q&A — mine for insight/reframes"),
  ("C","Amod/mental_health_counseling_conversations",""),
  ("C","facebook/empathetic_dialogues","emotional dialogue"),
  ("C","jerryjalapeno/nart-100k-synthetic","therapy-style"),
  # D — build-your-own (instruction breadth + persona/roleplay)
  ("D","tatsu-lab/alpaca",""),("D","OpenAssistant/oasst1",""),("D","OpenAssistant/oasst2",""),
  ("D","Open-Orca/SlimOrca",""),("D","garage-bAInd/Open-Platypus",""),
  ("D","google/Synthetic-Persona-Chat",""),("D","HuggingFaceH4/ultrachat_200k",""),
  ("D","WizardLMTeam/WizardLM_evol_instruct_70k","evolved instructions"),
  ("D","GAIR/lima","high-quality instructions"),("D","Open-Orca/OpenOrca","FLAN system-prompt"),
  ("D","teknium/OpenHermes-2.5","large high-quality instruction mix"),
  ("D","cognitivecomputations/dolphin","large instruction/uncensored"),
  # --- BIG general / voice corpora (volume + style base; all byte-capped) ---
  ("A","BEE-spoke-data/gutenberg-en-v1-clean","cleaned PD books — narrative voice (capped)"),
  ("B","abisee/cnn_dailymail","news + highlights summarization"),
  ("B","argilla/news-summary","news summarization"),
  ("C","webis/tldr-17","Reddit posts + TL;DR — real people working things out"),
  ("C","Anthropic/hh-rlhf","helpful/harmless dialogue (mine non-prescriptive)"),
  ("D","Open-Orca/OpenOrca","FLAN reasoning (deep sample)"),
]

# datasets that require an explicit config name
CONFIGS = {
  "abisee/cnn_dailymail": "3.0.0",
}

# ------------------------------------------------------- discovery keywords
KEYWORDS = {
  "A": ["meditation","mindfulness","guided imagery","relaxation","hypnosis","sleep story",
        "asmr","visualization","creative writing","short story","descriptive fiction","poetry",
        "storytelling","fantasy","imagination","calm","yoga nidra","bedtime story","narrative",
        "fairy tale","prose","scene description"],
  "B": ["summarization","email","paraphrase","rewrite","grammar","business writing",
        "letter writing","note taking","wikihow","editing","proofreading","headline",
        "report writing","meeting notes","productivity","text simplification","abstract"],
  "C": ["therapy","counseling","motivational interviewing","mental health","emotional support",
        "coaching","cognitive behavioral","psychology dialogue","reflective listening","advice",
        "self help","journaling","life coaching","stoicism","philosophy dialogue","socratic",
        "empathy","wellbeing","support conversation"],
  "D": ["instruction following","roleplay","persona","character","assistant conversation",
        "reasoning","multi-task instruction","system prompt","chat","dialogue","question answering",
        "task","tutorial","how to","explanation","conversational"],
}

def discover(sort, per_kw=150):
    """Pull the top reachable datasets per family keyword we don't already have."""
    from huggingface_hub import HfApi
    api = HfApi()
    pulled = 0
    for fam, kws in KEYWORDS.items():
        for kw in kws:
            try:
                if sort:
                    cand = list(api.list_datasets(search=kw, sort=sort, limit=per_kw))
                else:
                    cand = list(api.list_datasets(search=kw, limit=per_kw))  # relevance
            except Exception as e:
                # retry without sort if the sort key is unsupported
                try:
                    cand = list(api.list_datasets(search=kw, limit=per_kw))
                except Exception as e2:
                    log(f"discover query fail '{kw}': {str(e2)[:80]}"); continue
            for d in cand:
                if corpus_bytes() / 1e9 >= DISK_CAP_GB:
                    log("disk cap hit during discovery"); return pulled
                if have(fam, d.id): continue
                if grab(fam, d.id, note=f"discovered:{kw}:{sort}") > 0:
                    pulled += 1
    return pulled

# ------------------------------------------------------- main loop
if __name__ == "__main__":
    log(f"==== grind v2 start (disk cap {DISK_CAP_GB}GB, per-ds cap {PER_DATASET_CAP}) ====")
    log(f"current corpus: {corpus_bytes()/1e9:.2f} GB")
    # 1) seed list
    for fam, hid, note in SEED:
        if corpus_bytes() / 1e9 >= DISK_CAP_GB: break
        grab(fam, hid, note=note or "seed", config=CONFIGS.get(hid))
    # 2) discovery cycles, varied sort orders to widen each pass
    sorts = ["downloads", None, "likes", None, "downloads", None]
    for c in range(MAX_CYCLES):
        if corpus_bytes() / 1e9 >= DISK_CAP_GB:
            log("disk cap reached — stopping"); break
        s = sorts[c % len(sorts)]
        log(f"--- discovery cycle {c+1}/{MAX_CYCLES} (sort={s}) | corpus {corpus_bytes()/1e9:.2f} GB ---")
        got = discover(s)
        log(f"cycle {c+1}: +{got} datasets (corpus now {corpus_bytes()/1e9:.2f} GB)")
    # tally
    for fam, d in FAM_DIR.items():
        sz = sum(os.path.getsize(os.path.join(dp, f)) for dp, _, fs in os.walk(os.path.join(ROOT, d)) for f in fs)
        log(f"  {d}: {sz/1e6:.0f} MB")
    log(f"==== grind v2 done — total {corpus_bytes()/1e9:.2f} GB ====")
