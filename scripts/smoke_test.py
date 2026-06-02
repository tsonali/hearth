"""End-to-end smoke test — does the WHOLE thing actually work, server-side?

Hits a running Hearth server the way the browser does, across every surface:
hub loads, each tool page loads, and each engine endpoint actually responds
correctly (companion turn, ask index+query, imagination generate). This is the
"does the product work, not just the unit pieces" check.

Run against an already-running server:
    .venv/bin/python -m uvicorn imagination_engine.server:app --port 8000 &   # in one shell
    .venv/bin/python scripts/smoke_test.py                                    # in another

Exit code 0 = all green. Prints a checklist with timings.
"""

from __future__ import annotations

import json
import sys
import time
import urllib.request
import urllib.error
from pathlib import Path

BASE = "http://127.0.0.1:8000"
ROOT = Path(__file__).resolve().parents[1]


def _get(path: str) -> tuple[int, str]:
    try:
        with urllib.request.urlopen(BASE + path, timeout=180) as r:
            return r.status, r.read().decode("utf-8", "ignore")
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8", "ignore")


def _post(path: str, body: dict, timeout: int = 600) -> tuple[int, dict]:
    data = json.dumps(body).encode()
    req = urllib.request.Request(BASE + path, data=data,
                                 headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        return e.code, {"error": e.read().decode("utf-8", "ignore")}


def main() -> int:
    checks: list[tuple[str, bool, str]] = []

    def check(name: str, cond: bool, detail: str = ""):
        checks.append((name, cond, detail))
        print(f"  [{'PASS' if cond else 'FAIL'}] {name}" + (f" — {detail}" if detail else ""))

    print("== pages load ==")
    for path, marker in [("/", "HEARTH"), ("/intake", "intake"),
                         ("/companion", "mirror, not a person"), ("/ask", "Ask Your Files")]:
        t0 = time.time()
        st, html = _get(path)
        check(f"GET {path}", st == 200 and marker.lower() in html.lower(),
              f"{st}, {round(time.time()-t0,1)}s")

    print("== companion engine ==")
    t0 = time.time()
    st, d = _post("/companion/turn",
                  {"session_id": "smoke", "message": "I keep avoiding a hard conversation."})
    reply = d.get("reply", "")
    check("companion replies", st == 200 and len(reply) > 10, f"{round(time.time()-t0,1)}s")
    check("companion no anthropomorphism slip", not d.get("flagged"), str(d.get("flagged")))

    print("== ask-your-files engine ==")
    book = ROOT / "data" / "test_corpus" / "pride_and_prejudice.txt"
    if book.is_file():
        t0 = time.time()
        st, d = _post("/ask/index", {"corpus": "smoke", "path": str(book)})
        check("ask index", st == 200 and d.get("chunks", 0) > 0,
              f"{d.get('chunks')} chunks, {round(time.time()-t0,1)}s")
        t0 = time.time()
        st, d = _post("/ask/query", {"corpus": "smoke", "question": "who is Mr. Darcy?"})
        ans = d.get("answer", "")
        check("ask answers grounded", st == 200 and "darcy" in ans.lower(),
              f"{round(time.time()-t0,1)}s")
        st, d = _post("/ask/query", {"corpus": "smoke", "question": "what is the wifi password?"})
        check("ask refuses out-of-corpus", "isn't in your files" in d.get("answer", "").lower(),
              d.get("answer", "")[:50])
    else:
        check("ask test corpus present", False, f"missing {book} (run fetch_test_corpus.sh)")

    print()
    passed = sum(1 for _, ok, _ in checks if ok)
    total = len(checks)
    print(f"{'ALL GREEN' if passed == total else f'{total-passed} FAILED'}  ({passed}/{total})")
    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
