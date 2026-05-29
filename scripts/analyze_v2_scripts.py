"""Quantitative + qualitative analysis of the v2 scenario batch.

Walks every script in logs/scenario-tests/ and surfaces failure patterns:
- Hedging language frequency (the meditation-app sound)
- Stock peaceful imagery (the AI default for "peaceful")
- Word-salad tail (the 005-different-personality failure mode)
- Word count distribution + settle/body/return balance
- Generic-ending pattern (every script ends the same way)
- Scenarios where the engine dodged the prompt vs engaged it

Run from repo root:
    .venv/bin/python scripts/analyze_v2_scripts.py
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from collections import Counter

ROOT = Path("logs/scenario-tests")


# ---------------------------------------------------------------------------
# Patterns we count.
# ---------------------------------------------------------------------------

HEDGING_PATTERNS = [
    r"\byou might notice\b",
    r"\bperhaps\b",
    r"\bmaybe\b",
    r"\bif you'?d like\b",
    r"\bif you choose\b",
    r"\byou could\b",
    r"\bmay feel\b",
    r"\bmight feel\b",
    r"\bmight sense\b",
    r"\bnotice if\b",
    r"\bsee if\b",
    r"\bsee whether\b",
    r"\ballow yourself to\b",
    r"\bwhatever it is\b",
    r"\bwhatever you\b",
]

# The AI's stock "peaceful imagery" defaults — what shows up when the
# model retreats from the user's actual creative prompt.
STOCK_IMAGERY = [
    "candlelight", "candle", "candles",
    "meadow", "meadows", "rolling hills",
    "wildflowers", "wildflower",
    "brook", "babbling", "gurgling",
    "lavender", "honeysuckle",
    "sunshine", "sun-kissed", "sun kissed", "sunlit",
    "warm bath", "warm light",
    "dappled light", "dappled",
    "gentle breeze", "soft breeze",
    "nightingale", "songbird",
    "blooming",
    "stars overhead",
    "twinkling",
    "softly", "soft glow",
    "shimmering", "shimmer",
    "sun-kissed flowers",
]

# Words that signal the model has lost coherence (the 005 failure mode).
# These are nonsense-collocation patterns from real failures we've seen.
INCOHERENCE_TELLS = [
    r"\bsweetness profound\b",
    r"\bharmonies jar\b",
    r"\bsin flags\b",
    r"\bropes laughter\b",
    r"\bdully pulsing\b",
    r"\bemerald strip\b",
    r"\bcrisscrossed by morning dew\b",
    r"\bdrops beading in drops\b",
    # More generic: very long noun phrases with no verb structure
]

GENERIC_ENDINGS = [
    "welcome back",
    "wiggle",
    "open your eyes",
    "carry it with you",
    "carry this with",
    "live your day",
]


def count_hits(text: str, patterns: list[str]) -> int:
    n = 0
    for p in patterns:
        n += len(re.findall(p, text, flags=re.IGNORECASE))
    return n


def count_words(text: str, words: list[str]) -> int:
    """Count whole-word hits for a list of stock imagery terms."""
    n = 0
    lower = text.lower()
    for w in words:
        # Use word-ish boundaries that handle multi-word stock phrases
        n += len(re.findall(r"\b" + re.escape(w) + r"\b", lower))
    return n


def split_stages(script: str) -> tuple[str, str, str]:
    """Heuristic split of script into (settle, body, return).

    The body always starts with a transition line like "And now, you settle
    even more deeply" or "settle into the imaginary". The return always
    starts with "And now, slowly, that image begins to soften" or similar.
    """
    # Body starts at the first transition phrase
    body_starts = [
        r"\band now,?\s+you settle\b",
        r"\band now,?\s+as you settle\b",
        r"\bsettle into the imaginary\b",
        r"\bthe room around .*dissolves\b",
        r"\bthe room .*falls? away\b",
        r"\bsomewhere else begin\b",
        r"\binto this imaginary\b",
        r"\bthe imagining\b",
    ]
    # Return starts at the first softening phrase
    return_starts = [
        r"\band now,?\s+slowly,?\s+that image begins to soften\b",
        r"\bthat image begins to soften\b",
        r"\bthe image begins to soften\b",
        r"\band now,?\s+slowly,?\s+let",
        r"\bbring yourself back\b",
        r"\bnotice the breath again\b",
    ]

    body_idx = None
    for p in body_starts:
        m = re.search(p, script, flags=re.IGNORECASE)
        if m and (body_idx is None or m.start() < body_idx):
            body_idx = m.start()

    return_idx = None
    for p in return_starts:
        m = re.search(p, script, flags=re.IGNORECASE)
        if m and m.start() > (body_idx or 0):
            if return_idx is None or m.start() < return_idx:
                return_idx = m.start()

    if body_idx is None:
        return script, "", ""
    if return_idx is None:
        return script[:body_idx].strip(), script[body_idx:].strip(), ""
    return (
        script[:body_idx].strip(),
        script[body_idx:return_idx].strip(),
        script[return_idx:].strip(),
    )


def detect_word_salad(text: str) -> tuple[bool, str]:
    """Heuristic check for the 005 failure mode.

    Looks at the last 100 words; flags if (a) any specific incoherence tell
    fires, or (b) it has too many nouns in unusual collocations (the "metal
    stem sin flags" pattern).
    """
    words = text.split()
    tail = " ".join(words[-100:])
    for pat in INCOHERENCE_TELLS:
        if re.search(pat, tail, flags=re.IGNORECASE):
            return True, f"matched: {pat}"
    # Heuristic: avg sentence length in the tail > 35 words with no commas
    # is suspicious — but commas are common, so this rarely fires. Rely on
    # the named-pattern check.
    return False, ""


def per_thousand(n: int, total_words: int) -> float:
    return 1000.0 * n / max(total_words, 1)


def analyze() -> dict:
    """Walk all scenarios; return a summary dict."""
    rows = []
    for scen_dir in sorted(ROOT.iterdir()):
        if not scen_dir.is_dir():
            continue
        script_path = scen_dir / "script.txt"
        intake_path = scen_dir / "intake.txt"
        if not script_path.is_file():
            continue

        script = script_path.read_text(encoding="utf-8")
        intake = intake_path.read_text(encoding="utf-8") if intake_path.is_file() else ""

        settle, body, ret = split_stages(script)
        tw = len(script.split())
        sw, bw, rw = len(settle.split()), len(body.split()), len(ret.split())

        hedges = count_hits(script, HEDGING_PATTERNS)
        stock = count_words(script, STOCK_IMAGERY)
        gibberish, gib_reason = detect_word_salad(script)

        # Did the body engage the user's specific request?
        # Heuristic: pull a few keywords from the user's intake message
        # (the first one, before the engine's response) and see if they
        # appear in the body. Very rough but catches "user said Harry, body
        # never mentions Harry."
        user_prompt = ""
        if intake:
            # Lines after [USER] up to the next blank line / [ENGINE]
            m = re.search(
                r"\[USER\]\s*\n(.*?)(?:\n\s*\[ENGINE\]|\Z)",
                intake,
                flags=re.DOTALL,
            )
            if m:
                user_prompt = m.group(1).strip()

        # Pull content words from the user prompt: nouns/adjectives/verbs.
        # Crude: anything 4+ chars, not stop words.
        stop = {
            "imagine", "this", "that", "those", "these", "with", "want",
            "have", "they", "them", "there", "where", "when", "what",
            "from", "into", "your", "yours", "their", "very", "much",
            "more", "less", "really", "being", "myself", "yourself",
            "would", "could", "should", "about", "around", "right",
            "well", "just", "make", "made",
        }
        prompt_keywords = [
            w.lower() for w in re.findall(r"[A-Za-z']{4,}", user_prompt)
            if w.lower() not in stop
        ][:6]
        body_lower = body.lower()
        engaged = sum(1 for k in prompt_keywords if k in body_lower)
        engage_rate = engaged / max(len(prompt_keywords), 1)

        rows.append({
            "name": scen_dir.name,
            "prompt_keywords": prompt_keywords,
            "engaged_keywords": engaged,
            "engage_rate": round(engage_rate, 2),
            "total_words": tw,
            "settle_words": sw,
            "body_words": bw,
            "return_words": rw,
            "hedges": hedges,
            "hedges_per_1000": round(per_thousand(hedges, tw), 1),
            "stock_imagery": stock,
            "stock_per_1000": round(per_thousand(stock, tw), 1),
            "gibberish_tail": gibberish,
            "gibberish_reason": gib_reason,
        })

    rows.sort(key=lambda r: r["name"])
    return {"count": len(rows), "scenarios": rows}


def summarize(result: dict) -> None:
    rows = result["scenarios"]
    n = len(rows)

    def avg(key):
        return sum(r[key] for r in rows) / n if n else 0

    def med(key):
        vals = sorted(r[key] for r in rows)
        return vals[n // 2] if n else 0

    print(f"\n=== batch summary: {n} scripts ===\n")
    print(f"  word count:  median {int(med('total_words'))}   mean {int(avg('total_words'))}")
    print(f"    settle:    median {int(med('settle_words'))}   mean {int(avg('settle_words'))}")
    print(f"    body:      median {int(med('body_words'))}    mean {int(avg('body_words'))}")
    print(f"    return:    median {int(med('return_words'))}    mean {int(avg('return_words'))}")
    print()
    print(f"  hedging:     mean {avg('hedges'):.1f}/script   ({avg('hedges_per_1000'):.1f} per 1000 words)")
    print(f"  stock img:   mean {avg('stock_imagery'):.1f}/script   ({avg('stock_per_1000'):.1f} per 1000 words)")
    print(f"  engage rate: {avg('engage_rate'):.2f}  (body contains user-prompt keywords)")
    print()

    gibberish_scripts = [r for r in rows if r["gibberish_tail"]]
    print(f"  gibberish-tail failures: {len(gibberish_scripts)}/{n}")
    for r in gibberish_scripts:
        print(f"    {r['name']}: {r['gibberish_reason']}")
    print()

    # Worst offenders by hedging rate
    print("  top-10 hedging-rate offenders:")
    for r in sorted(rows, key=lambda x: -x["hedges_per_1000"])[:10]:
        print(f"    {r['hedges_per_1000']:5.1f}/1k  {r['name']}")
    print()

    # Worst offenders by stock imagery
    print("  top-10 stock-imagery offenders:")
    for r in sorted(rows, key=lambda x: -x["stock_per_1000"])[:10]:
        print(f"    {r['stock_per_1000']:5.1f}/1k  {r['name']}")
    print()

    # Scripts where the body didn't engage the user's prompt
    print("  worst engage-rate (body ignored user's prompt keywords):")
    for r in sorted(rows, key=lambda x: x["engage_rate"])[:15]:
        kw = ",".join(r["prompt_keywords"][:4])
        print(f"    {r['engage_rate']:.2f}  {r['name']}  (keywords: {kw})")
    print()

    # Total-word outliers (the 005 type — short)
    print("  shortest scripts (potential generation failures):")
    for r in sorted(rows, key=lambda x: x["total_words"])[:10]:
        print(f"    {r['total_words']:4d} words   {r['name']}")


if __name__ == "__main__":
    p = argparse.ArgumentParser(description="Mechanical (no-LLM) failure-mode analysis of a script batch.")
    p.add_argument("dir", nargs="?", default=str(ROOT),
                   help="scenario-tests directory to analyze (default: logs/scenario-tests)")
    args = p.parse_args()
    ROOT = Path(args.dir)
    if not ROOT.is_dir():
        print(f"not a directory: {ROOT}", file=sys.stderr)
        sys.exit(1)
    print(f"analyzing: {ROOT}")
    result = analyze()
    summarize(result)
    out = ROOT / "ANALYSIS.json"
    out.write_text(json.dumps(result, indent=2))
    print(f"\nFull per-scenario data: {out}")
