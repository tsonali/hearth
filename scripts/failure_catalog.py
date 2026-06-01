"""Failure catalog — mine a corpus for WHERE THE ENGINE EMPIRICALLY FALLS DOWN.

The disciplined gap-finding step: before designing elicitation or more engine
fixes, find the REAL failures (not imagined ones). This goes past pass/fail
curation — it categorizes HOW each script fails and flags the ones a human should
read, so we end with an evidence-based map of what to fix.

Mechanical signals (no model): repetition, hedging, stock imagery, length,
word-salad, prompt-engagement (did the body use the user's own words?), and
anchor-leakage (did it copy the prompt's example phrases?).

    .venv/bin/python scripts/failure_catalog.py logs/corpus-v6_2

Writes <dir>/FAILURE-CATALOG.json + prints: per-failure-mode tallies, the worst
offenders per mode, and a prioritized READ LIST (scripts most worth a human read).
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[0]))
from analyze_v2_scripts import (  # noqa: E402
    count_hits, count_words, repetition_score, detect_word_salad,
    HEDGING_PATTERNS, STOCK_IMAGERY,
)

# Phrases that are TEACHING EXAMPLES in our prompts — if they appear in output,
# the model copied them literally (the anchor-leakage failure).
LEAK_PHRASES = [
    "warmth across the top of your sternum", "late-afternoon orange", "fluorescent buzz",
    "the radiator clicking", "his laugh from the next room",
    "the muscle behind your right shoulder blade", "weight on your left hip",
    "silver bodysuit", "the in-ear monitor", "forty thousand",
]

STOP = {"imagine","that","this","with","your","yourself","being","about","just",
        "want","really","like","what","when","where","have","from","into","them",
        "they","then","than","some","very","feel","feels"}


def prompt_engagement(script: str, intake: str) -> float:
    """Fraction of the user's content-words that appear in the script body."""
    m = re.search(r"\[USER\]\s*\n(.+?)(?:\n\s*\[ENGINE\]|\Z)", intake, flags=re.DOTALL)
    seed = (m.group(1) if m else intake).lower()
    kws = [w for w in re.findall(r"[a-z']{4,}", seed) if w not in STOP][:8]
    if not kws:
        return 1.0
    body = script.lower()
    return round(sum(1 for k in kws if k in body) / len(kws), 2)


def catalog_one(script: str, intake: str) -> dict:
    words = len(script.split())
    rep, rep_ex = repetition_score(script)
    hedges = count_hits(script, HEDGING_PATTERNS)
    stock = count_words(script, STOCK_IMAGERY)
    salad, _ = detect_word_salad(script)
    engage = prompt_engagement(script, intake)
    leaks = [p for p in LEAK_PHRASES if p in script.lower()]

    modes = []
    if rep > 0.30: modes.append("repetition")
    if words < 1400: modes.append("too_short")
    if words > 3200: modes.append("too_long")
    if hedges > 4: modes.append("hedging")
    if stock > 3: modes.append("stock_imagery")
    if salad: modes.append("word_salad")
    if engage < 0.4: modes.append("low_prompt_engagement")
    if leaks: modes.append("anchor_leakage")

    # read-priority: more/again worse failure modes => more worth a human read.
    # also flag CLEAN-but-interesting (passed everything) lightly for spot-reads.
    priority = len(modes) * 10 + (5 if rep > 0.25 else 0) + (5 if engage < 0.5 else 0)
    return {"words": words, "repetition": rep, "hedges": hedges, "stock": stock,
            "engagement": engage, "leaks": leaks, "failure_modes": modes,
            "read_priority": priority, "rep_examples": rep_ex[:2]}


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("dir")
    args = p.parse_args()
    root = Path(args.dir)
    if not root.is_dir():
        print(f"not a directory: {root}", file=sys.stderr); return 1

    rows = []
    for d in sorted(x for x in root.iterdir() if x.is_dir()):
        sp, ip = d / "script.txt", d / "intake.txt"
        if not sp.is_file():
            continue
        rec = catalog_one(sp.read_text(encoding="utf-8"),
                          ip.read_text(encoding="utf-8") if ip.is_file() else "")
        rec["id"] = d.name
        rows.append(rec)

    mode_counts = Counter(m for r in rows for m in r["failure_modes"])
    clean = [r for r in rows if not r["failure_modes"]]
    out = {"dir": str(root), "scored": len(rows), "clean": len(clean),
           "failure_mode_tallies": dict(mode_counts.most_common()),
           "scripts": sorted(rows, key=lambda r: -r["read_priority"])}
    (root / "FAILURE-CATALOG.json").write_text(json.dumps(out, indent=2))

    print(f"\n=== failure catalog: {root.name} ===")
    print(f"  scored {len(rows)}  ·  clean (no mechanical failure) {len(clean)}  ·  "
          f"{100*len(clean)//max(len(rows),1)}% clean")
    print("\n  failure modes (how many scripts hit each):")
    for mode, n in mode_counts.most_common():
        print(f"    {n:3d}  {mode}")
    print("\n  READ LIST (highest-priority human reads — worst/most failures):")
    for r in sorted(rows, key=lambda r: -r["read_priority"])[:12]:
        if r["read_priority"] == 0: break
        print(f"    [{r['read_priority']:3d}] {r['id']}: {', '.join(r['failure_modes'])}")
    print(f"\n  wrote {root/'FAILURE-CATALOG.json'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
