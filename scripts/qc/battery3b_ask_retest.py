#!/usr/bin/env python3
"""QC Battery 3b — re-test the three Ask-Your-Files fixes:
words-bridge (sauce=ragù), meaningful citations, re-index replaces stale facts."""
import os, shutil, time
from fastapi.testclient import TestClient
import imagination_engine.server as s

c = TestClient(s.app)
ROOT = "/tmp/hearth_qc_corpus3b"

def ask(corpus, q):
    a = c.post("/ask/query", json={"corpus": corpus, "question": q}).json()
    print(f"\nQ: {q}\nA: {a.get('answer')}\n   [sources={a.get('sources')}]", flush=True)
    return a

shutil.rmtree(ROOT, ignore_errors=True)
os.makedirs(ROOT)
open(os.path.join(ROOT, "recipes.txt"), "w").write(
    "NONNA'S RAGU: 2 lbs beef chuck, 1 lb pork shoulder. Brown hard, deglaze with a cup "
    "of dry white wine (NOT red, she was adamant). San Marzano tomatoes, 4 hours minimum "
    "at a bare simmer. Salt only at the end.\n")
open(os.path.join(ROOT, "finances.txt"), "w").write(
    "Mortgage payment is $3,240 a month, due on the 5th.\n"
    "Emergency fund: $18,500 in the Ally savings account.\n")
open(os.path.join(ROOT, "work.txt"), "w").write(
    "Q3 signups 4,200 against a 3,500 target. Marta owns retention. Next review October 2.\n")

t0 = time.time()
print("#### words-bridge + citation quality", flush=True)
c.post("/ask/index", json={"corpus": "qc3b", "path": ROOT})
a = ask("qc3b", "What kind of wine goes in the sauce my grandmother made?")
print("  BRIDGE:", "PASS" if "white" in (a.get("answer") or "").lower() else "FAIL", flush=True)
a = ask("qc3b", "How long does my grandmother's pasta sauce need to cook?")
print("  BRIDGE2 (unassisted):", "PASS" if "4 hours" in (a.get("answer") or "").lower() else "FAIL", flush=True)
a = ask("qc3b", "How much is the mortgage payment?")
srcs = a.get("sources") or []
print("  CITATION:", "PASS" if srcs and len(srcs) <= 2 and "finances.txt" in srcs[0]
      else f"FAIL {srcs}", flush=True)

print("\n#### re-index replaces stale facts", flush=True)
open(os.path.join(ROOT, "work.txt"), "w").write(
    "Q3 signups 4,200 against a 3,500 target. Deshawn took over retention from Marta. "
    "Next review moved to November 14.\n")
c.post("/ask/index", json={"corpus": "qc3b", "path": ROOT})
a = ask("qc3b", "When is the next review?")
ans = (a.get("answer") or "").lower()
print("  STALE:", "PASS" if "november 14" in ans and "october" not in ans else "FAIL", flush=True)
a = ask("qc3b", "Who owns retention?")
print("  OWNER:", "PASS" if "deshawn" in (a.get("answer") or "").lower() else "FAIL", flush=True)
print(f"\ntotal {time.time()-t0:.0f}s", flush=True)
