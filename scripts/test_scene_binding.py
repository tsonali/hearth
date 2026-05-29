"""Tests for scene-binding (PR #2) — the mechanism, not the LLM output.

Verifies the deterministic pieces the generator relies on: archetype
round-trips through Classification, bibles load + render a bound context block,
beats derive from the bible, and an empty/unknown archetype yields no bible
(the improvise fallback). LLM behavior (does the classifier pick the right
archetype, does the bound scene read as immersive) is validated separately on
the grind box — that needs a model run; this does not.

Run: .venv/bin/python scripts/test_scene_binding.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from imagination_engine.comprehension import Classification  # noqa: E402
from imagination_engine.scene_bibles import get_bible, archetype_names  # noqa: E402

MAX_BEATS = 12  # mirror generator.MAX_BEATS


def _derive_beats(bible):
    """Mirror the generator's bible→beats derivation, to test it in isolation."""
    return [
        (b.description + (f" [function: {b.function}]" if b.function else "")).strip()
        for b in bible.beats
        if b.description.strip()
    ][:MAX_BEATS]


def run() -> int:
    failures = 0

    def check(name, cond, detail=""):
        nonlocal failures
        print(f"  [{'ok' if cond else 'FAIL'}] {name}" + (f" — {detail}" if detail and not cond else ""))
        failures += 0 if cond else 1

    print("== archetype round-trips through Classification ==")
    c = Classification(direction="case_a", subject="Taylor Swift", archetype="backstage-pre-show")
    d = c.to_dict()
    check("to_dict carries archetype", d.get("archetype") == "backstage-pre-show", str(d))
    check("from_dict restores archetype",
          Classification.from_dict(d).archetype == "backstage-pre-show")
    check("from_dict tolerates missing archetype",
          Classification.from_dict({"direction": "case_c"}).archetype == "")

    print("== bible loads + binds ==")
    arches = archetype_names()
    check("at least one bible available", len(arches) >= 1, str(arches))
    bible = get_bible("backstage-pre-show")
    check("get_bible('backstage-pre-show') loads", bible is not None)
    if bible is not None:
        ctx = bible.context_block()
        check("context_block names the archetype",
              ctx.startswith("SCENE ARCHETYPE: backstage-pre-show"), ctx[:60])
        check("context_block is substantive", len(ctx) > 100, f"len={len(ctx)}")
        check("bible has anchors", len(bible.anchors) >= 1, f"{len(bible.anchors)} anchors")
        check("bible has beats", len(bible.beats) >= 1, f"{len(bible.beats)} beats")

        beats = _derive_beats(bible)
        check("beats derive to non-empty strings",
              len(beats) >= 1 and all(isinstance(b, str) and b for b in beats),
              str(beats[:2]))
        check("beats capped at MAX_BEATS", len(beats) <= MAX_BEATS)

    print("== no-match → improvise fallback ==")
    # the generator does: bible = get_bible(archetype) if archetype else None
    check("empty archetype yields no bible", get_bible("") is None)
    check("unknown archetype yields no bible", get_bible("does-not-exist") is None)

    print(f"\n{'ALL PASS' if failures == 0 else f'{failures} FAILURE(S)'}")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(run())
