#!/usr/bin/env python3
"""Score Family-A candidate scripts for CONCRETENESS — the curation bar.

The corpus read found the failure mode precisely: good imagery COMMITS to specific
physical, sensory things; bad ("AI-y") imagery retreats to abstraction ("a sense of
calm," "present moment," "let go of negativity") and meta-talk ("Welcome to this
meditation"). This scores each candidate so we can rank a big pile and pull the
genuinely-vivid ones into the A gold set — curate, don't dump.

Score is rough but discriminating: reward concrete/sensory/second-person language,
penalize abstraction and meta-talk, per 100 words. NOT a substitute for a human read
— it's a SIEVE that surfaces the top candidates to read.
"""
import json, os, re, sys, glob

ROOT = os.path.expanduser("~/Downloads/hearth-corpus")
A = os.path.join(ROOT, "A-imagination")

CONCRETE = re.compile(r"\b(feel|feeling|notice|see|look|watch|hear|listen|touch|smell|"
  r"taste|skin|hand|hands|finger|fingers|feet|foot|toes|face|jaw|shoulder|shoulders|"
  r"chest|stomach|belly|back|neck|eyes|eyelids|forehead|breath|breathe|arms|legs|knees|"
  r"palms|lips|tongue|teeth|scalp|spine|muscles|floor|ground|chair|bed|window|door|wall|"
  r"ceiling|water|sand|sun|tree|trees|leaf|leaves|grass|stone|rock|path|breeze|rain|"
  r"warmth|cold|warm|cool|rough|smooth|soft|heavy|weight|blanket|pillow|table|cup|mug|"
  r"room|wood|wooden|salt|damp|bark|petal|stream|shore|wave|waves|step|steps)\b", re.I)

ABSTRACT = re.compile(r"\b(sense of|presence|energy|journey|essence|awareness|inner peace|"
  r"\bpeace\b|calmness|negativity|positivity|positive energy|present moment|mindful|"
  r"mindfulness|intention|gratitude|serenity|tranquil|tranquility|embrace|nurtur|nourish|"
  r"healing light|divine|universe|soul|spirit|vibration|abundance|manifest|oneness|"
  r"let go of|release the|deep relaxation|sense of calm|state of)\b", re.I)

AIY_META = re.compile(r"(welcome to|i'?m (so )?glad|take this time for yourself|"
  r"in this (meditation|session)|today we|let'?s begin our|thank you for joining|"
  r"this guided|in today'?s|as we begin this)", re.I)

# GUIDED-SCRIPT signal — second-person, present-tense, directing a listener. This is
# what makes it a SESSION (vs. a GoT scene, a poem, or code that merely has nouns).
GUIDED = re.compile(r"\b(close your eyes|your eyes|notice|imagine|picture|breathe|"
  r"your breath|take a (deep |slow )?breath|feel your|let yourself|let your|"
  r"bring your attention|allow your|allow yourself|as you breathe|with each breath|"
  r"you find yourself|relax your|you can feel|you can hear|you can see|you begin to|"
  r"gently|slowly|notice how|you are (standing|sitting|lying|walking|here))\b", re.I)
# code / markup junk — skip outright
CODE = re.compile(r"(import |def |class |\bself\.|<\/?\w+>|function\s*\(|;\s*$|{\s*$|"
  r"console\.|print\(|return |#include|public static)", re.I)


def script_text(rec):
    if isinstance(rec, str): return rec
    if isinstance(rec, dict):
        cands = [v for v in rec.values() if isinstance(v, str)]
        return max(cands, key=len) if cands else ""
    return ""


def score(text):
    words = text.split()
    n = len(words)
    if n < 150 or n > 3000:        # a session, not a fragment or a 29k-word doc
        return None
    if CODE.search(text[:400]):    # skip code/markup
        return None
    per = 100.0 / n
    c = len(CONCRETE.findall(text)) * per
    a = len(ABSTRACT.findall(text)) * per
    m = len(AIY_META.findall(text)) * per
    g = len(GUIDED.findall(text)) * per
    if g < 1.5:                    # GATE: must read as a guided second-person script
        return None
    sc = round(2.0 * c + 4.0 * g - 3.0 * a - 8.0 * m, 2)
    return sc, round(c, 1), round(a, 1), round(m, 2), n, round(g, 1)


scored = []
for path in glob.glob(os.path.join(A, "**", "*.jsonl"), recursive=True) + \
            glob.glob(os.path.join(A, "**", "*.txt"), recursive=True):
    name = os.path.relpath(path, A)
    if path.endswith(".txt"):
        recs = [open(path, encoding="utf-8", errors="ignore").read()]
    else:
        try:
            recs = [json.loads(l) for l in open(path, encoding="utf-8", errors="ignore")]
        except Exception:
            continue
    for i, r in enumerate(recs[:5000]):
        t = script_text(r)
        s = score(t)
        if s:
            scored.append((s[0], name, i, s[1], s[2], s[3], s[4], s[5], t))

scored.sort(reverse=True)
print(f"scored {len(scored)} GUIDED scripts (150-3000w, second-person) across "
      f"{len(set(x[1] for x in scored))} files\n")
print("="*70 + "\nTOP 15 (concrete AND guided — gold candidates)\n" + "="*70)
for sc, name, i, c, a, m, n, g, t in scored[:15]:
    print(f"\n[score {sc}  concrete={c} guided={g} abstract={a} aiy={m}  {n}w]  {name}#{i}")
    print("  " + re.sub(r"\s+", " ", t[:240]).strip())
print("\n" + "="*70 + "\nBOTTOM 5 (guided but abstract/AI-y — the failure mode)\n" + "="*70)
for sc, name, i, c, a, m, n, g, t in scored[-5:]:
    print(f"\n[score {sc}  concrete={c} abstract={a} aiy={m}]  {name}#{i}")
    print("  " + re.sub(r"\s+", " ", t[:220]).strip())

# write ranked gold-candidate index (top 200) for the next curation pass
out = os.path.join(ROOT, "_manifests", "a_gold_candidates.jsonl")
cut = scored[:200]
with open(out, "w") as f:
    for sc, name, i, c, a, m, n, g, t in cut:
        f.write(json.dumps({"score": sc, "file": name, "idx": i, "words": n,
                            "concrete": c, "guided": g, "abstract": a, "aiy": m,
                            "text": t}, ensure_ascii=False) + "\n")
print(f"\nwrote top {len(cut)} candidates -> {out}")
# which source files the gold candidates come from (where the real scripts live)
from collections import Counter
src = Counter(x[1] for x in scored[:200])
print("\nTOP SOURCE FILES among the 200 best guided scripts:")
for f, ct in src.most_common(12):
    print(f"  {ct:3d}  {f}")
