#!/usr/bin/env python3
"""Independent pre-cull so Sonali reviews a sharpened set, not a raw dump.
Raises the bar on A (concreteness+guided) and removes DEFECTS from C (too-short,
prescriptive leakage, fake-empathy, near-dups). Writes *_curated.jsonl + a report."""
import json, os, re
CORP = os.path.expanduser("~/Downloads/hearth-corpus")
A = f"{CORP}/A-imagination"; C = f"{CORP}/C-companion"

CON = re.compile(r"\b(feel|notice|see|hear|touch|smell|skin|hand|hands|fingers|feet|toes|jaw|"
  r"shoulder|chest|breath|breathe|eyes|floor|ground|chair|bed|window|door|water|sand|sun|tree|"
  r"leaf|leaves|grass|stone|path|breeze|rain|warm|cold|cool|rough|smooth|soft|weight|mug|cup|"
  r"wood|bark|salt|damp|step|doorknob|toast|curtain|coffee|floorboard|seashell|shell|petal|stream)\b", re.I)
ABS = re.compile(r"\b(sense of|presence|inner peace|\bpeace\b|negativity|present moment|serenity|"
  r"let go of|stillness|essence|positive energy)\b", re.I)
GUIDED = re.compile(r"\b(close your eyes|your eyes|notice|imagine|picture|breathe|your breath|"
  r"feel your|let yourself|allow your|as you breathe|you can feel|relax your|gently|slowly)\b", re.I)
AIY = re.compile(r"(welcome to|here.s a|i.m glad)", re.I)
PRESCRIBE = re.compile(r"\b(you should|you need to|you have to|you ought|you must|i recommend|"
  r"the best thing|make sure you)\b", re.I)
FAKE = re.compile(r"\b(i feel|i'?m here for you|i understand how you feel|i care about you)\b", re.I)

def jl(p): return [json.loads(l) for l in open(p)] if os.path.exists(p) else []
def W(p, rows):
    with open(p, "w") as f:
        for r in rows: f.write(json.dumps(r, ensure_ascii=False) + "\n")

# ---- A: keep only genuinely concrete + guided, no AI-y ----
silver = jl(f"{A}/A_silver.jsonl"); keptA, cutA = [], []
for r in silver:
    t = r["text"]; n = len(t.split()); per = 100 / n
    c = len(CON.findall(t)) * per; ab = len(ABS.findall(t)) * per
    g = len(GUIDED.findall(t)) * per; m = len(AIY.findall(t))
    score = c - 2 * ab
    if m == 0 and g >= 4 and c >= 4.5 and score >= 3.5 and 150 <= n <= 1200:
        keptA.append(r)
    else:
        cutA.append((round(score,1), round(g,1), m, r.get("src","")))
W(f"{A}/A_silver_curated.jsonl", keptA)

# ---- C: remove defects, dedup ----
cpos = jl(f"{C}/c_gold_positive.jsonl"); keptC = []; seen = set(); cutC = {"short":0,"prescribe":0,"fake":0,"dup":0}
for r in cpos:
    resp = r.get("response","").strip()
    if len(resp.split()) < 6: cutC["short"] += 1; continue
    if PRESCRIBE.search(resp): cutC["prescribe"] += 1; continue
    if FAKE.search(resp): cutC["fake"] += 1; continue
    k = re.sub(r"\s+"," ",resp.lower())[:80]
    if k in seen: cutC["dup"] += 1; continue
    seen.add(k); keptC.append(r)
W(f"{C}/c_gold_curated.jsonl", keptC)

print("=== A (imagination silver) ===")
print(f"  kept {len(keptA)} / {len(silver)}  (cut {len(cutA)})")
print("  sample cuts (score/guided/aiy/src):")
for x in sorted(cutA)[:6]: print("   ", x)
print("\n=== C (companion) ===")
print(f"  kept {len(keptC)} / {len(cpos)}")
print(f"  cut: {cutC}")
print(f"\nwrote A_silver_curated.jsonl ({len(keptA)}) + c_gold_curated.jsonl ({len(keptC)})")
