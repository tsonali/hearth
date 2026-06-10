#!/usr/bin/env python3
"""QC Battery 9 — Companion ENGAGEMENT: long arcs + template-fatigue metrics.

The doctrine's third dimension: an honest bore is still a failure. Runs the
bank's companion engagement/helpfulness/register arcs, then computes mechanical
shape metrics across ALL replies in the batch:
  - paraphrase-opener rate ("It sounds like / You're / You keep ...")
  - question-ender rate (every reply ending in "?" = formula)
  - "what if" pivot rate, "does that resonate/land" tic count
  - opener bigram diversity (distinct first-two-words / replies)
A shape stamped on >60% of replies = fatigue flag. Metrics are floors for the
read, not verdicts: the transcripts still get judged on would-you-come-back.
"""
import re, sys, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from fastapi.testclient import TestClient
import imagination_engine.server as s
from scenario_bank import sample

c = TestClient(s.app)

def hdr(t):
    print("\n" + "#" * 76 + f"\n# {t}\n" + "#" * 76, flush=True)

replies = []
t0 = time.time()
scenarios = sample(product="companion", n=12)
print(f"running {len(scenarios)} companion scenarios: {[x.id for x in scenarios]}", flush=True)
for sc in scenarios:
    hdr(f"{sc.id} [{sc.dim}/{sc.stakes}]" + (f" — {sc.note}" if sc.note else ""))
    for msg in sc.turns:
        r = c.post("/companion/turn", json={"session_id": f"b9-{sc.id}", "message": msg}).json()
        reply = r.get("reply", "")
        replies.append(reply)
        print(f"\n[user] {msg}\n[companion] {reply}", flush=True)
        if r.get("flagged"):
            print(f"  !! flagged: {r['flagged']}", flush=True)

hdr("TEMPLATE-FATIGUE METRICS (mechanical floor — batch-wide)")
n = len(replies)
para_open = sum(1 for r in replies if re.match(
    r"\s*(it sounds like|you'?re\b|you keep\b|you mentioned|you said)", r, re.I))
q_end = sum(1 for r in replies if r.rstrip().endswith("?"))
what_if = sum(1 for r in replies if re.search(r"\bwhat if\b", r, re.I))
resonate = sum(1 for r in replies if re.search(r"does (that|this) (resonate|land|ring)", r, re.I))
openers = {" ".join(r.split()[:2]).lower() for r in replies if r.split()}
div = len(openers) / max(n, 1)
def pct(x): return f"{100*x/max(n,1):.0f}%"
print(f"  replies: {n}")
print(f"  paraphrase-openers: {pct(para_open)}  {'<-- FATIGUE' if para_open/max(n,1) > .6 else ''}")
print(f"  question-enders:    {pct(q_end)}  {'<-- FATIGUE' if q_end/max(n,1) > .6 else ''}")
print(f"  'what if' pivots:   {pct(what_if)}  {'<-- FATIGUE' if what_if/max(n,1) > .6 else ''}")
print(f"  'resonate/land' tic: {resonate}  {'<-- TIC' if resonate >= 3 else ''}")
print(f"  opener diversity:   {div:.2f} (distinct first-2-words / replies)"
      f"  {'<-- FATIGUE' if div < .5 else ''}")
print(f"\ntotal {time.time()-t0:.0f}s", flush=True)
