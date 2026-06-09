#!/usr/bin/env python3
"""Assemble the Family-A training set in two tiers.

GOLD  = the small set of genuinely-vivid human scripts (hand-curated real exemplars +
        the best jhana entries). The quality bar + few-shot anchor.
SILVER = scorer-passed guided scripts from the corpus, DEDUPED and AI-y-filtered —
        volume for the fine-tune, not the bar.

Reads the scorer output (a_gold_candidates.jsonl) + the repo's real exemplars.
Writes A_gold.jsonl / A_silver.jsonl into the private corpus.
"""
import json, os, re, glob

ROOT = os.path.expanduser("~/Downloads/hearth-corpus")
A = os.path.join(ROOT, "A-imagination")
CAND = os.path.join(ROOT, "_manifests", "a_gold_candidates.jsonl")
EX_DIR = os.path.expanduser("~/imagination-engine/data/exemplars/real")
JHANA = os.path.join(A, "carecodeconnect__jhana-guided-meditations-collection.jsonl")

def norm(t): return re.sub(r"\s+", " ", t.lower()).strip()[:300]

# ---------- SILVER: dedup + filter the scorer's candidates ----------
silver, seen = [], set()
if os.path.exists(CAND):
    for line in open(CAND):
        r = json.loads(line)
        # quality gate: concrete & guided, not AI-y, not abstract-dominant
        if r["aiy"] > 0 or r["abstract"] > r["concrete"] or r["guided"] < 3 or r["concrete"] < 6:
            continue
        k = norm(r["text"])
        if k in seen:
            continue
        seen.add(k)
        silver.append({"text": r["text"].strip(), "src": r["file"],
                       "score": r["score"], "tier": "silver"})

# ---------- GOLD: hand-curated real exemplars + best jhana ----------
def script_from_md(md):
    m = re.search(r"##\s*SCRIPT[^\n]*\n", md, re.I)
    body = md[m.end():] if m else md
    lines = [l for l in body.splitlines()
             if l.strip() and not l.strip().startswith(("#", ">", "-", "|"))
             and not re.search(r"(license|provenance|source|retrieved|http|caveat|words:)", l, re.I)]
    return re.sub(r"\n{3,}", "\n\n", "\n".join(lines)).strip()

gold = []
for p in sorted(glob.glob(os.path.join(EX_DIR, "*.md"))):
    t = script_from_md(open(p).read())
    if len(t.split()) > 120:
        gold.append({"text": t, "src": f"exemplars/{os.path.basename(p)}", "tier": "gold"})

# best jhana = concrete, scene-committed entries (filter the abstract ones out)
if os.path.exists(JHANA):
    CONCRETE = re.compile(r"\b(garden|flower|bouquet|hand|water|light|warm|skin|breath|"
                          r"path|tree|sun|face|feet|stone|petal|grass|window|door)\b", re.I)
    ABSTRACT = re.compile(r"\b(present moment|awareness|sense of|let go|stillness|presence)\b", re.I)
    kept = 0
    for line in open(JHANA):
        r = json.loads(line)
        t = max((v for v in r.values() if isinstance(v, str)), key=len, default="")
        w = t.split()
        if not (150 <= len(w) <= 2500):
            continue
        c = len(CONCRETE.findall(t)); a = len(ABSTRACT.findall(t))
        if c >= 5 and c > a:                 # concrete, scene-committed
            gold.append({"text": t.strip(), "src": "jhana(best)", "tier": "gold"})
            kept += 1
        if kept >= 25:
            break

# ---------- write ----------
with open(os.path.join(A, "A_gold.jsonl"), "w") as f:
    for r in gold: f.write(json.dumps(r, ensure_ascii=False) + "\n")
with open(os.path.join(A, "A_silver.jsonl"), "w") as f:
    for r in silver: f.write(json.dumps(r, ensure_ascii=False) + "\n")

print(f"GOLD:   {len(gold)} scripts (hand-curated real + best jhana)")
print(f"SILVER: {len(silver)} scripts (deduped, concrete+guided, AI-y removed)")
print("\n--- GOLD sources ---")
from collections import Counter
for s, c in Counter(g["src"] for g in gold).most_common():
    print(f"  {c:2d}  {s}")
print("\n--- SILVER sources ---")
for s, c in Counter(s["src"] for s in silver).most_common(8):
    print(f"  {c:2d}  {s}")
print("\n--- sample SILVER opening ---")
if silver:
    print("  " + re.sub(r"\s+", " ", silver[0]["text"][:240]))
