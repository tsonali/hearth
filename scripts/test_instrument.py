"""Test Part D — build / persist / reopen / use a personal instrument.

The 'build your own' flow: describe an instrument + point it at files -> it grounds
+ persists -> reopen by name (fresh) -> use it in persona, grounded in the files.
Proves the standing, return-to-it property that defines Part D.
    .venv/bin/python scripts/test_instrument.py
"""
from __future__ import annotations

import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from imagination_engine.instrument import (  # noqa: E402
    InstrumentRegistry, build_instrument, open_instrument)
from imagination_engine.inference import Engine  # noqa: E402


def run() -> int:
    tmp = Path(tempfile.mkdtemp())
    wf = tmp / "work"; wf.mkdir()
    (wf / "budget.txt").write_text("Leadership approved 1.2 million extra for the platform team.")
    (wf / "churn.txt").write_text("Onboarding friction, not price, drives churn in the first two weeks.")
    reg = InstrumentRegistry(tmp / "registry.sqlite")
    eng = Engine.load()
    fails = 0

    build_instrument(reg, name="work-associate", created="2026-06-01",
                     description="a concise assistant who knows my work files", files=wf)
    listed = [s.name for s in reg.list()]
    print(f"  [{'ok' if 'work-associate' in listed else 'FAIL'}] persisted + listed: {listed}")
    fails += 0 if "work-associate" in listed else 1

    inst = open_instrument(eng, reg, "work-associate")
    print(f"  [{'ok' if inst else 'FAIL'}] reopened by name")
    fails += 0 if inst else 1

    if inst:
        a = inst.ask("what did we decide about the platform team budget?")
        ok = "1.2 million" in a or "1,200,000" in a or "1.2m" in a.lower()
        print(f"  [{'ok' if ok else 'FAIL'}] grounded answer: {a[:90]!r}")
        fails += 0 if ok else 1

        # out-of-files question -> should refuse, not invent
        a2 = inst.ask("what is our parental leave policy?")
        refused = "isn't in your files" in a2.lower() or "not in your files" in a2.lower()
        print(f"  [{'ok' if refused else 'FAIL'}] refuses out-of-files: {a2[:70]!r}")
        fails += 0 if refused else 1

    print(f"\n{'ALL PASS' if fails == 0 else f'{fails} FAILURE(S)'}")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(run())
