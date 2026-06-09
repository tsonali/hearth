#!/usr/bin/env python3
"""Promote concrete generated A candidates into A_silver.jsonl (dedup + score gate)."""
import json, os, re
A = os.path.expanduser("~/Downloads/hearth-corpus/A-imagination/")
GEN, SILVER = A + "A_generated.jsonl", A + "A_silver.jsonl"

CON = re.compile(r"\b(feel|notice|see|hear|touch|smell|skin|hand|hands|fingers|feet|toes|jaw|"
  r"shoulder|chest|breath|breathe|eyes|floor|ground|chair|bed|window|door|water|sand|sun|tree|"
  r"leaf|leaves|grass|stone|path|breeze|rain|warm|cold|cool|rough|smooth|soft|weight|mug|cup|"
  r"wood|bark|salt|damp|step|doorknob|toast|curtain|coffee|floorboard)\b", re.I)
ABS = re.compile(r"\b(sense of|presence|inner peace|\bpeace\b|negativity|present moment|serenity|"
  r"let go of|stillness|essence)\b", re.I)
AIY = re.compile(r"(welcome to|here.s a|i.m glad)", re.I)

def norm(t): return re.sub(r"\s+", " ", t.lower()).strip()[:160]

existing = set()
if os.path.exists(SILVER):
    for l in open(SILVER):
        try: existing.add(norm(json.loads(l).get("text", "")))
        except Exception: pass

promoted = skipped = 0
with open(SILVER, "a") as out:
    for l in open(GEN):
        r = json.loads(l); t = r["text"]; k = norm(t)
        if k in existing: skipped += 1; continue
        n = len(t.split()); per = 100 / n
        sc = len(CON.findall(t)) * per - 2 * len(ABS.findall(t)) * per - 5 * len(AIY.findall(t)) * per
        if sc >= 2.5 and len(AIY.findall(t)) == 0:
            existing.add(k)
            out.write(json.dumps({"text": t.strip(), "src": "generated-fewshot",
                "score": round(sc, 1), "tier": "silver-generated",
                "intake": r.get("intake"), "protocol": r.get("protocol")}, ensure_ascii=False) + "\n")
            promoted += 1
print(f"promoted {promoted} (skipped {skipped} dups/low-score); A_silver total = "
      f"{sum(1 for _ in open(SILVER))}")
