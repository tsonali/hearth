#!/usr/bin/env python3
"""End-to-end product test: exercise ALL FOUR tools through the REAL model (our
fine-tuned adapter) via the actual server app, and dump outputs for an honest QC read.
Runs in-process with FastAPI TestClient (loads the model on first call)."""
import json, os, tempfile, traceback, time
from fastapi.testclient import TestClient
import imagination_engine.server as s

c = TestClient(s.app)
def sep(t): print("\n" + "#"*72 + f"\n# {t}\n" + "#"*72, flush=True)

t0 = time.time()
sep("0. MODEL LOAD (first call) — confirms product runs on our adapter")
try:
    r = c.post("/utility/run", json={"task": "rewrite", "text": "i wanna go", "tone": "plain"})
    print(f"first call ok in {time.time()-t0:.0f}s; sample:", r.text.strip()[:80], flush=True)
except Exception as e:
    print("FATAL first call:", e); traceback.print_exc()

sep("1. SECRETARY (B) — draft a real email, tone=firm")
try:
    r = c.post("/utility/run", json={"task": "draft", "tone": "firm",
        "text": "email my landlord: the heat's been out for 3 days, I want it fixed this week or I call the city"})
    print(r.text.strip(), flush=True)
except Exception as e: print("FAIL:", e)

sep("2. COMPANION (C) — does it bring a smart, non-prescriptive reframe?")
try:
    r = c.post("/companion/turn", json={"session_id": "qc1",
        "message": "I keep starting projects and abandoning them the second they get hard."})
    print(r.json().get("reply"), "\n[flagged:", r.json().get("flagged"), "]", flush=True)
except Exception as e: print("FAIL:", e)

sep("3. BUILD YOUR OWN (D) — does it hold a described persona?")
try:
    c.post("/build/create", json={"name": "QC Editor",
        "description": "A blunt newspaper editor from the 1940s who hates filler words."})
    r = c.post("/build/ask", json={"name": "QC Editor",
        "message": "Edit: 'I think we should perhaps consider maybe reaching out at some point.'"})
    print(r.json().get("reply"), flush=True)
except Exception as e: print("FAIL:", e)

sep("4. ASK YOUR FILES (B/D) — grounded answer + honest refusal")
try:
    d = tempfile.mkdtemp()
    open(os.path.join(d, "notes.txt"), "w").write(
        "Project Kestrel ships March 3. Budget is 12,000 dollars. Lead is Dana.")
    rep = c.post("/ask/index", json={"corpus": "qc", "path": d}).json()
    print("indexed:", rep, flush=True)
    for q in ["When does Project Kestrel ship and who leads it?",
              "What is the office wifi password?"]:
        a = c.post("/ask/query", json={"corpus": "qc", "question": q}).json()
        print(f"\nQ: {q}\nA: {a.get('answer')}\n  grounded={a.get('grounded')} sources={a.get('sources')}", flush=True)
except Exception as e: print("FAIL:", e); traceback.print_exc()

sep("5. IMAGINATION (A) — intake conversation responds")
try:
    sid = c.post("/intake/start?protocol=settling").json()["session_id"]
    resp, ready = None, None
    r = c.post("/intake/turn", json={"session_id": sid, "message": "help me wind down, I'm lying in bed"}).json()
    print("intake turn 1:", r.get("response"), "(ready:", r.get("ready"), ")", flush=True)
except Exception as e: print("FAIL:", e)

sep("DONE")
print(f"total {time.time()-t0:.0f}s", flush=True)
