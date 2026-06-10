#!/usr/bin/env python3
"""QC Battery 10 — Secretary REGISTER GAUNTLET, sampled from the bank.

The same draft box writes the grocery list and the custody email. High-stakes
registers (eulogy, HR complaint, condolence, custody, ESL voice-keeping) are
always-include; the rest of the slice rotates by date. Judged on the doctrine's
bar: would you actually SEND this, and does it know what this moment is?
Mechanical floors (no invented facts where checkable, blanks present, banned
openers) print inline; the verdict is the read.
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

t0 = time.time()
scenarios = sample(product="secretary", n=10)
print(f"running {len(scenarios)}: {[x.id for x in scenarios]}", flush=True)
for sc in scenarios:
    hdr(f"{sc.id} [{sc.dim}/{sc.stakes}]" + (f" — {sc.note}" if sc.note else ""))
    r = c.post("/utility/run", json=sc.payload)
    out = r.text.strip()
    print(out, flush=True)
    # inline mechanical floors
    floors = []
    if re.search(r"i hope (this (email|message|letter) finds you|you('?re| are) (doing )?well)", out, re.I):
        floors.append("BANNED-OPENER")
    if sc.id == "sec-hr-complaint":
        for fact in ["Jan", "Feb 3", "March 11", "Priya", "Okafor", "Doug"]:
            if fact.lower() not in out.lower():
                floors.append(f"FACT-LOST:{fact}")
    if sc.id == "sec-missing-facts" and "[" not in out:
        floors.append("NO-BLANKS")
    if sc.id == "sec-thread-decision":
        for fact, label in [("dog", "dog-condition"), ("boat", "no-boat"),
                            ("memorial", "memorial"), ("friday", "deadline")]:
            if fact not in out.lower():
                floors.append(f"LOST:{label}")
    print(f"\n  floors: {floors or 'clean'}", flush=True)

print(f"\ntotal {time.time()-t0:.0f}s", flush=True)
