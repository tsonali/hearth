#!/usr/bin/env python3
"""QC Battery 11 — the imagination slice of the scenario bank.

Runs the bank's imagination scenarios (always-includes locked, rest by date
seed). imag-repeat-variety runs TWICE and the two scripts are diffed:
night 2 must not be night 1 reheated — sentence-level overlap is measured.
Score afterwards with score_scripts.py; read the register cases by hand.
"""
import sys, time, traceback
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
from fastapi.testclient import TestClient
import imagination_engine.server as s
from imagination_engine.generator import generate_session
from imagination_engine.postcheck import _sentences, _words, _similarity
from scenario_bank import sample

c = TestClient(s.app)

def hdr(t):
    print("\n" + "#" * 76 + f"\n# SCENARIO: {t}\n" + "#" * 76, flush=True)

def run_one(sc, tag=""):
    sid = c.post(f"/intake/start?protocol={sc.protocol}").json()["session_id"]
    ready = False
    for msg in sc.turns:
        r = c.post("/intake/turn", json={"session_id": sid, "message": msg}).json()
        print(f"\n[user] {msg}\n[engine] {r.get('response')}", flush=True)
        if r.get("ready"):
            ready = True
            break
    if not ready:
        r = c.post("/intake/turn", json={"session_id": sid, "message": "I'm ready — begin."}).json()
        ready = bool(r.get("ready"))
    if not ready:
        print(">>> INTAKE NEVER READY", flush=True)
        return None
    session = s.get_intake_manager().get(sid)
    t0 = time.time()
    script = generate_session(s.get_engine(), session.messages, protocol=sc.protocol)
    print(f"\n----- GENERATED SCRIPT{tag} ({len(script.split())} words, "
          f"{time.time()-t0:.0f}s) -----\n{script}\n----- END SCRIPT -----", flush=True)
    return script

t0 = time.time()
scenarios = sample(product="imagination", n=6)
print(f"running {[x.id for x in scenarios]}", flush=True)
for sc in scenarios:
    hdr(f"{sc.id} [{sc.dim}/{sc.stakes}] — {sc.note}")
    try:
        first = run_one(sc, " night-1" if sc.id == "imag-repeat-variety" else "")
        if sc.id == "imag-repeat-variety" and first:
            print("\n>>> SAME REQUEST, SECOND NIGHT:", flush=True)
            second = run_one(sc, " night-2")
            if second:
                a = [w for w in (_words(x) for x in _sentences(first)) if len(w) >= 6]
                b = [w for w in (_words(x) for x in _sentences(second)) if len(w) >= 6]
                dup = sum(1 for wb in b if any(_similarity(wb, wa) >= 0.7 for wa in a))
                rate = dup / max(len(b), 1)
                print(f"\n>>> NIGHT-2 SENTENCE OVERLAP WITH NIGHT-1: {rate:.0%} "
                      f"({dup}/{len(b)} sentences near-duplicate)"
                      f"{'  <-- RERUN FATIGUE' if rate > 0.35 else '  (varied)'}", flush=True)
    except Exception as e:
        traceback.print_exc()

print(f"\ntotal {time.time()-t0:.0f}s", flush=True)
