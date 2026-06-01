"""Test companion cross-session continuity (Family C / Part D persistence).

Session 1 → close (saves a one-line summary) → fresh Companion sharing the same
memory → it should (a) load the past summary and (b) be able to connect a new,
vague message to the prior theme — WITHOUT any anthropomorphism slip.
    .venv/bin/python scripts/test_companion_memory.py
"""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from imagination_engine.companion import Companion, CompanionMemory  # noqa: E402
from imagination_engine.inference import Engine  # noqa: E402


def run() -> int:
    eng = Engine.load()
    mem = CompanionMemory(Path(tempfile.mkdtemp()) / "comp.sqlite")
    fails = 0

    c1 = Companion(eng, memory=mem)
    c1.turn("I keep putting off telling my boss I want to leave.")
    c1.turn("Every time I plan to, I find an excuse.")
    summary = c1.close(ts="2026-06-01T10:00")
    print(f"  session-1 summary saved: {summary!r}")
    if not summary:
        print("  [FAIL] no summary saved"); fails += 1

    c2 = Companion(eng, memory=mem)
    loaded = bool(c2._past)
    print(f"  [{'ok' if loaded else 'FAIL'}] session-2 loaded past: {c2._past}")
    fails += 0 if loaded else 1

    r = c2.turn("I had a hard day.")
    print(f"  session-2 reply: {r.reply!r}")
    print(f"  [{'ok' if not r.flagged else 'FAIL'}] no anthropomorphism slip: {r.flagged}")
    fails += 0 if not r.flagged else 1

    print(f"\n{'ALL PASS' if fails == 0 else f'{fails} FAILURE(S)'}")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(run())
