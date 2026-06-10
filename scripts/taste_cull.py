#!/usr/bin/env python3
"""Re-cull A against Sonali's demonstrated taste (from her A_review.md notes):
 - no preachy/explanatory intro (start in the scene)
 - no conclusory abstractions (gratitude, 'may all beings be happy', loving-kindness)
 - no meta-commentary that breaks immersion ('at first it can be difficult')
 - no random named people / odd refs (Ken, Phillip, Buddha House, green gorge)
 - no non-prose junk (JSON/knowledge-graph blobs)
 - one clean concrete scene that won't confuse the model
Outputs survivors + cuts-with-reason."""
import json, os, re, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))
from imagination_engine.postcheck import find_collapsed_paragraphs, find_degeneration_start
A = os.path.expanduser("~/Downloads/hearth-corpus/A-imagination")
jl = lambda p: [json.loads(l) for l in open(p)] if os.path.exists(p) else []

PREACHY = re.compile(r"(this (guided )?(practice|meditation|exercise|session)|loving.?kindness|"
    r"\bmetta\b|the benefits of|research (shows|has shown)|welcome to|today we will|"
    r"in this (exercise|session|meditation)|begin this practice)", re.I)
ABSTRACT_END = re.compile(r"(may all beings|be happy\b|gratitude|loving.?kindness|the practice\b|"
    r"compassion for all|namaste|gassho|inner peace|your true self|sense of gratitude)", re.I)
META = re.compile(r"(at first it (can|may) be difficult|some people find|you might find this hard|"
    r"it (can|may) be hard at first|don'?t worry if)", re.I)
ODD = re.compile(r"(buddha house|green gorge|\bken\b|phillip|rejoic|all beings everywhere)", re.I)
NOTPROSE = re.compile(r'("node_|"label"|"name"|\{|\}|node_1|->|\bdef\b)')

def first_words(t, n=45): return " ".join(t.split()[:n])

def judge(t):
    head = first_words(t)
    if NOTPROSE.search(t[:300]): return "CUT", "non-prose junk (JSON/graph/code)"
    # Decay culls (added 2026-06-10 after the QC campaign): training on the
    # model's own broken-record loops or run-on grammar collapse REINFORCES
    # them — these never enter the corpus, however vivid the clean part is.
    if find_degeneration_start(t) is not None: return "CUT", "degenerate repetition loop"
    if find_collapsed_paragraphs(t): return "CUT", "run-on grammar collapse"
    if PREACHY.search(head):     return "CUT", "preachy/explanatory intro"
    if META.search(t):           return "CUT", "immersion-breaking meta-commentary"
    if ODD.search(t):            return "CUT", "random name / odd reference"
    if ABSTRACT_END.search(" ".join(t.split()[-60:])): return "CUT", "conclusory abstraction at end"
    # metta 'think of someone you' fan-out structure she disliked
    if t.lower().count("think of someone") + t.lower().count("bring them to mind") >= 2:
        return "CUT", "metta loving-kindness fan-out (not a scene)"
    return "KEEP", ""

rows = []
for tier_file, tier in [("A_gold.jsonl","gold"), ("A_silver.jsonl","silver"),
                        ("A_qc_harvest.jsonl","silver")]:
    for r in jl(f"{A}/{tier_file}"):
        t = re.sub(r"\[\d+(\.\d+)?\]","",r["text"]).strip()
        # strip provenance/frontmatter contamination (Sonali caught the va-001 leak)
        t = "\n".join(ln for ln in t.splitlines()
                      if not re.match(r'^(title|author_credit|protocol|concrete_nouns_test|'
                                      r'status|intake|words|license|source|url|caveat|note)\s*:',
                                      ln.strip(), re.I)
                      and not re.search(r'(Whole Health for Pain|Office of Patient Centered|'
                                        r'VA-employee|September 1, 2016|A HANDWARMING GUIDED|VHA /)',
                                        ln, re.I)).strip()
        v, why = judge(t)
        rows.append((v, tier, r.get("src",""), r.get("intake") or "", why, t))

keep = [r for r in rows if r[0]=="KEEP"]
cut  = [r for r in rows if r[0]=="CUT"]
from collections import Counter
print(f"KEEP {len(keep)} / {len(rows)}   CUT {len(cut)}")
print("\ncut reasons:", dict(Counter(r[4] for r in cut)))
print("\nsurvivors by source:", dict(Counter(r[1]+":"+(r[2].split('__')[0] if '__' in r[2] else r[2][:16]) for r in keep)))
# write the taste-curated set
with open(f"{A}/A_taste_curated.jsonl","w") as f:
    for v,tier,src,intake,why,t in keep:
        f.write(json.dumps({"text":t,"src":src,"tier":tier,"intake":intake}, ensure_ascii=False)+"\n")
print(f"\nwrote A_taste_curated.jsonl ({len(keep)})")
print("\n--- 3 survivor openings (sanity check they're clean scenes) ---")
for v,tier,src,intake,why,t in keep[:3]:
    print(f"\n[{tier}|{src[:30]}] {first_words(t,40)}")
