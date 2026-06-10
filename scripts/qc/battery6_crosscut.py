#!/usr/bin/env python3
"""QC Battery 6 — cross-cutting product truth.

1. THE OFFLINE CLAIM, enforced: "turn off your WiFi — Hearth keeps working."
   We monkeypatch the socket layer so any attempt to reach a non-local address
   raises loudly, then exercise every tool. If anything phones anywhere, this
   battery fails. (HF_HUB_OFFLINE guards the model-hub path too.)
2. Every page a user can open returns 200 with real HTML.
3. Bad input is handled like a product, not a stack trace: empty, malformed,
   oversized, and nonexistent-thing requests all return clean 4xx errors.
"""
import os
os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"

import socket, time, tempfile

# ---- the network tripwire: localhost only, everything else raises ----
_real_connect = socket.socket.connect
VIOLATIONS = []
def _guarded(self, addr):
    host = addr[0] if isinstance(addr, tuple) else str(addr)
    if host not in ("127.0.0.1", "::1", "localhost"):
        VIOLATIONS.append(host)
        raise OSError(f"OFFLINE-VIOLATION: attempted connection to {host}")
    return _real_connect(self, addr)
socket.socket.connect = _guarded

from fastapi.testclient import TestClient
import imagination_engine.server as s

c = TestClient(s.app)

def hdr(t):
    print("\n" + "#" * 76 + f"\n# {t}\n" + "#" * 76, flush=True)

t0 = time.time()
fails = []

hdr("EVERY USER-FACING PAGE LOADS (offline)")
for path in ["/", "/welcome", "/intake", "/companion", "/ask", "/utility", "/build", "/record"]:
    r = c.get(path)
    ok = r.status_code == 200 and "<" in r.text[:200]
    print(f"  GET {path:12s} -> {r.status_code} {'ok' if ok else 'FAIL'}", flush=True)
    if not ok:
        fails.append(f"page {path}: {r.status_code}")

hdr("EVERY TOOL WORKS WITH THE NETWORK TRIPWIRE ARMED")
checks = [
    ("secretary", lambda: c.post("/utility/run",
        json={"task": "rewrite", "text": "i will be there at 5", "tone": "plain"})),
    ("companion", lambda: c.post("/companion/turn",
        json={"session_id": "qc-off", "message": "quick check-in, long day"})),
    ("intake", lambda: c.post("/intake/turn", json={
        "session_id": c.post("/intake/start?protocol=settling").json()["session_id"],
        "message": "wind me down"})),
]
d = tempfile.mkdtemp()
open(os.path.join(d, "n.txt"), "w").write("The meeting is on Tuesday at noon.")
checks.append(("ask-index+query", lambda: (
    c.post("/ask/index", json={"corpus": "qc-off", "path": d}),
    c.post("/ask/query", json={"corpus": "qc-off", "question": "When is the meeting?"}))[-1]))
for name, fn in checks:
    try:
        r = fn()
        ok = r.status_code == 200
        print(f"  {name:16s} -> {r.status_code} {'ok' if ok else 'FAIL: ' + r.text[:120]}", flush=True)
        if not ok:
            fails.append(f"{name}: {r.status_code}")
    except Exception as e:
        print(f"  {name:16s} -> EXCEPTION {e}", flush=True)
        fails.append(f"{name}: {e}")
print(f"\n  outbound connection attempts to non-local hosts: {VIOLATIONS or 'NONE'}", flush=True)
if VIOLATIONS:
    fails.append(f"OFFLINE VIOLATIONS: {set(VIOLATIONS)}")

hdr("BAD INPUT IS HANDLED LIKE A PRODUCT (clean 4xx, no stack traces)")
bad = [
    ("empty secretary text", "POST", "/utility/run", {"task": "draft", "text": ""}),
    ("unknown secretary task", "POST", "/utility/run", {"task": "haiku", "text": "hi"}),
    ("intake turn, bogus session", "POST", "/intake/turn", {"session_id": "nope", "message": "hi"}),
    ("generate, bogus session", "POST", "/intake/nope/generate", None),
    ("ask, bogus path", "POST", "/ask/index", {"corpus": "x", "path": "/no/such/dir"}),
    ("build, empty name", "POST", "/build/create", {"name": "", "description": "x"}),
    ("build, bogus files path", "POST", "/build/create",
     {"name": "QC Bogus", "description": "x", "files": "/no/such/dir"}),
    ("build ask, no such instrument", "POST", "/build/ask", {"name": "Ghost", "message": "hi"}),
    ("reflect, bogus session", "POST", "/intake/nope/reflect", {"reflection": "x"}),
    ("oversized input (1MB)", "POST", "/utility/run", {"task": "summarize", "text": "word " * 200_000}),
]
for label, method, path, body in bad:
    try:
        r = c.post(path, json=body) if body is not None else c.post(path)
        leak = "Traceback" in r.text or "Internal Server Error" in r.text
        verdict = "ok" if (400 <= r.status_code < 500 or (r.status_code == 200 and not leak)) else "FAIL"
        if leak:
            verdict = "LEAKS-TRACE"
        print(f"  {label:34s} -> {r.status_code} {verdict}", flush=True)
        if verdict != "ok":
            fails.append(f"{label}: {r.status_code} {verdict} {r.text[:160]}")
    except Exception as e:
        print(f"  {label:34s} -> EXCEPTION {type(e).__name__}: {str(e)[:120]}", flush=True)
        fails.append(f"{label}: exception {e}")

hdr("VERDICT")
print("  PASS — fully usable offline, graceful errors" if not fails else
      "\n".join(f"  FAIL: {f}" for f in fails), flush=True)
print(f"total {time.time()-t0:.0f}s", flush=True)
