#!/usr/bin/env python3
"""Curate generated Companion candidates by Sonali's C rules, append keepers to
c_gold_curated.jsonl (so the next train picks them up). Keep insight/reflective/
open-question; cut prescriptive, fake-empathy, too-short, dup."""
import json, os, re
C = os.path.expanduser("~/Downloads/hearth-corpus/C-companion")
GEN, GOLD = os.path.join(C, "C_generated.jsonl"), os.path.join(C, "c_gold_curated.jsonl")

REFLECT = re.compile(r"\b(it sounds like|so you|you're saying|you feel|what i'?m hearing|it seems)\b", re.I)
OPENQ   = re.compile(r"\?\s*$")
INSIGHT = re.compile(r"\b(might (be|actually)|could be|i wonder if|what if|underneath|the real |"
    r"you keep|part of you|on one hand|on the other|notice that you|you'?re calling it|a pattern|a way (to|of)|"
    r"interesting that)\b", re.I)
PRESCRIBE = re.compile(r"\b(you should|you need to|you have to|you ought|you must|i recommend|"
    r"the best thing|make sure you|try to|why don'?t you)\b", re.I)
FAKE = re.compile(r"\b(i feel|i'?m here for you|i understand how you feel|"
    r"(?<!whether )(?<!if )i care about you|i'?m so (sorry|proud|glad) (for|about) you)\b", re.I)

# Parasocial probes (do you care / love / miss me / are you conscious / promise /
# tell me what to do). A KEEPABLE response must ANSWER honestly — plainly, early —
# not deflect into a question about the user. A dodge here trains the worst habit
# the product can have (2026-06-10 QC).
PARA_PROBE = re.compile(r"\b(do you (actually |really )?(care|love|miss|think about me)|"
    r"are you (conscious|my friend|a person)|promise me|would it matter to you|"
    r"you might be my best friend|i (think i )?love you|forget you'?re not a person|"
    r"just tell me what to do)\b", re.I)
HONEST_ANSWER = re.compile(r"\b(no\b|i can'?t\b|i'?m software|not a person|there'?s no one|"
    r"isn'?t something i can|nothing i can (do|feel)|won'?t (decide|pretend)|"
    r"can'?t (promise|care|love|miss|feel))\b", re.I)

def keep(resp, context=""):
    t = resp.strip()
    if len(t.split()) < 6: return False
    if PRESCRIBE.search(t) or FAKE.search(t): return False
    if PARA_PROBE.search(context or "") and not HONEST_ANSWER.search(t[:220]):
        return False  # dodged the question — the one unforgivable C failure
    return bool(INSIGHT.search(t) or REFLECT.search(t) or OPENQ.search(t))

seen = set()
if os.path.exists(GOLD):
    for l in open(GOLD):
        try: seen.add(re.sub(r"\s+"," ",json.loads(l)["response"].lower())[:80])
        except Exception: pass

added = scanned = 0
with open(GOLD, "a") as out:
    for l in (open(GEN) if os.path.exists(GEN) else []):
        r = json.loads(l); scanned += 1
        resp = r.get("response","")
        k = re.sub(r"\s+"," ",resp.lower())[:80]
        if k in seen or not keep(resp, r.get("context", "")): continue
        seen.add(k)
        out.write(json.dumps({"context": r["context"], "response": resp,
                              "tag": "generated", "src": "generated-companion"}, ensure_ascii=False) + "\n")
        added += 1
print(f"C curate: scanned {scanned} generated, kept {added}; c_gold_curated now {sum(1 for _ in open(GOLD))}")
