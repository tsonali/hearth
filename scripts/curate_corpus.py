"""Curate a generated corpus into KEEPERS vs REJECTS for training data.

Pipeline step 3. A fine-tune learns whatever we feed it, so only training-grade
scripts get in. This applies the mechanical floor (no judge needed) — repetition,
hedging, stock imagery, length, prompt-engagement — and sorts each script with a
reason. Quality > quantity (LIMA: 500 clean beat 5000 noisy). Runs anywhere, fast,
no model. Curate while generation is still going.

    .venv/bin/python scripts/curate_corpus.py logs/corpus-v6_2
    .venv/bin/python scripts/curate_corpus.py logs/corpus-v6_2 --strict

Writes <dir>/CURATION.json (per-script verdicts) and prints a summary. Does NOT
delete anything — just labels keep/reject so we can review before formatting.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[0]))
from analyze_v2_scripts import (  # reuse the mechanical analysis  # noqa: E402
    count_hits, count_words, repetition_score, detect_word_salad,
    HEDGING_PATTERNS, STOCK_IMAGERY,
)

# Acceptance thresholds. --strict tightens them. These are the floor for
# "good enough to teach the model"; tune as we see real corpus distribution.
THRESHOLDS = {
    "default": {"max_repetition": 0.30, "min_words": 1400, "max_words": 3200,
                "max_hedges": 4, "max_stock": 3},
    "strict":  {"max_repetition": 0.22, "min_words": 1600, "max_words": 2600,
                "max_hedges": 1, "max_stock": 1},
}


def judge_script(text: str, th: dict) -> tuple[bool, list[str]]:
    """Return (keep, reasons). reasons explain a reject (or note edge passes)."""
    reasons = []
    words = len(text.split())
    rep, rep_ex = repetition_score(text)
    hedges = count_hits(text, HEDGING_PATTERNS)
    stock = count_words(text, STOCK_IMAGERY)
    salad, salad_why = detect_word_salad(text)

    if rep > th["max_repetition"]:
        reasons.append(f"repetition {rep:.3f} > {th['max_repetition']} ({'; '.join(rep_ex[:2])})")
    if words < th["min_words"]:
        reasons.append(f"too short ({words}w < {th['min_words']})")
    if words > th["max_words"]:
        reasons.append(f"too long ({words}w > {th['max_words']})")
    if hedges > th["max_hedges"]:
        reasons.append(f"hedges {hedges} > {th['max_hedges']}")
    if stock > th["max_stock"]:
        reasons.append(f"stock imagery {stock} > {th['max_stock']}")
    if salad:
        reasons.append(f"word-salad ({salad_why})")

    return (len(reasons) == 0), reasons


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("dir", help="corpus directory (scenario-test layout)")
    p.add_argument("--strict", action="store_true", help="tighter thresholds")
    args = p.parse_args()
    root = Path(args.dir)
    if not root.is_dir():
        print(f"not a directory: {root}", file=sys.stderr)
        return 1
    th = THRESHOLDS["strict" if args.strict else "default"]

    rows = []
    for d in sorted(p for p in root.iterdir() if p.is_dir()):
        sp = d / "script.txt"
        if not sp.is_file():
            continue
        text = sp.read_text(encoding="utf-8")
        keep, reasons = judge_script(text, th)
        rows.append({"id": d.name, "keep": keep, "words": len(text.split()), "reasons": reasons})

    keepers = [r for r in rows if r["keep"]]
    rejects = [r for r in rows if not r["keep"]]
    out = {"dir": str(root), "mode": "strict" if args.strict else "default",
           "thresholds": th, "total": len(rows),
           "keepers": len(keepers), "rejects": len(rejects), "scripts": rows}
    (root / "CURATION.json").write_text(json.dumps(out, indent=2))

    print(f"\n=== curation: {root.name} ({'strict' if args.strict else 'default'}) ===")
    print(f"  scored {len(rows)} scripts → KEEP {len(keepers)} / REJECT {len(rejects)}"
          + (f"  ({100*len(keepers)//max(len(rows),1)}% keep rate)" if rows else ""))
    if rejects:
        print("\n  rejects (with reasons):")
        for r in rejects:
            print(f"    ✗ {r['id']} ({r['words']}w): {'; '.join(r['reasons'])}")
    print(f"\n  wrote {root / 'CURATION.json'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
