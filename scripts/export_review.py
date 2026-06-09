#!/usr/bin/env python3
"""Export the taste-critical training data into readable, markable docs for Sonali.
A (imagination scripts) + C (companion insight pairs). She marks KEEP/CUT/FIX;
her edits feed the next fine-tune. B/D are commodity — not exported for review."""
import json, os, re

CORP = os.path.expanduser("~/Downloads/hearth-corpus")
OUT = os.path.expanduser("~/Downloads")
_TIMING = re.compile(r"\[\d+(\.\d+)?\]")
def clean(t): return _TIMING.sub("", t).strip()

def jl(p):
    return [json.loads(l) for l in open(p, encoding="utf-8")] if os.path.exists(p) else []

# ---------- A: imagination scripts ----------
gold = jl(f"{CORP}/A-imagination/A_gold.jsonl")
silver = jl(f"{CORP}/A-imagination/A_silver.jsonl")
gen = [r for r in silver if r.get("tier") == "silver-generated"]
corp = [r for r in silver if r.get("tier") != "silver-generated"]

with open(f"{OUT}/A_review.md", "w") as f:
    f.write("# A — Imagination scripts, for review\n\n"
            "Mark each: **KEEP / CUT / FIX (note)**. Your edits drive the next fine-tune.\n"
            "Gold = hand-vetted real + best jhana. Generated = our few-shot output. "
            "Corpus = scorer-passed from the wild.\n\n---\n\n")
    def block(title, rows):
        f.write(f"\n# {title} ({len(rows)})\n\n")
        for i, r in enumerate(rows, 1):
            tag = r.get("intake") or r.get("src", "")
            f.write(f"## {title[:3]}-{i}  ·  _{tag}_  ·  [{r.get('src','')}]\n\n"
                    f"> **verdict:** \n\n{clean(r['text'])}\n\n---\n\n")
    block("GOLD", gold)
    block("GENERATED (few-shot)", gen)
    block("CORPUS (scorer-passed)", corp)

# ---------- C: companion insight pairs ----------
cpos = jl(f"{CORP}/C-companion/c_gold_positive.jsonl")
insight = [r for r in cpos if r.get("tag") == "insight"]
other = [r for r in cpos if r.get("tag") != "insight"]
with open(f"{OUT}/C_review.md", "w") as f:
    f.write("# C — Companion pairs, for review\n\n"
            "Does the response bring a real, *smart* move (reframe / pattern / possibility) "
            "and hand it back — never prescribing, never faking feelings? Mark KEEP/CUT.\n"
            "Showing all 'insight'-tagged pairs + a sample of the reflective ones.\n\n---\n\n")
    f.write(f"# INSIGHT pairs ({len(insight)})\n\n")
    for i, r in enumerate(insight, 1):
        f.write(f"## C-{i}\n\n**Them:** {r['context'].replace(chr(10),' ')[:400]}\n\n"
                f"**It:** {r['response']}\n\n> **verdict:** \n\n---\n\n")
    f.write(f"\n# REFLECTIVE/OPEN-Q sample ({min(len(other),60)} of {len(other)})\n\n")
    for i, r in enumerate(other[:60], 1):
        f.write(f"## R-{i}\n\n**Them:** {r['context'].replace(chr(10),' ')[:300]}\n\n"
                f"**It:** {r['response']}\n\n---\n\n")

for name in ("A_review.md", "C_review.md"):
    p = f"{OUT}/{name}"
    print(f"{name}: {os.path.getsize(p)//1000} KB")
print(f"\nA: gold {len(gold)} | generated {len(gen)} | corpus {len(corp)}")
print(f"C: insight {len(insight)} | reflective {len(other)}")
print(f"-> open ~/Downloads/A_review.md and ~/Downloads/C_review.md")
