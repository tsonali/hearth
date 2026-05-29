"""Immersion-rubric scorer — LLM-as-judge for guided-imagination scripts.

The keyword-counting analyzer (`analyze_v2_scripts.py`) catches known
failure modes — hedging, stock imagery, prompt-disengagement. Necessary
floor, not a score. A script can have zero hedges and zero meadows and
still be flat.

This scorer asks an LLM judge to read each script and score five
dimensions on a 1-5 scale:

  PRESENCE      Did you feel "I am there" while reading? (1=flat narration, 5=full transport)
  COMMITMENT    Does it state what's happening directly, or hedge? (1=hedgy meditation-app voice, 5=committed direct)
  EMBODIMENT    Is the listener positioned correctly given the user's intake? (1=wrong subject, 5=exactly right)
  SENSORY       How specific are the sensory details? (1=abstract feelings, 5=body-part / object-noun specifics)
  SPECIFICITY   Is this the user's actual scene, or stock content? (1=generic peaceful, 5=specifically the asked-for scene)

For each script the judge returns JSON: scores + a one-sentence reason
per dimension + an overall verdict.

Usage:
    .venv/bin/python scripts/score_immersion.py logs/scenario-tests-v4/
    .venv/bin/python scripts/score_immersion.py logs/scenario-tests-v3/ logs/scenario-tests-v4/

Writes `IMMERSION-SCORES.json` (per-script details) and prints a summary
table. When given two directories, prints a head-to-head delta table.
"""

from __future__ import annotations

import argparse
import json
import logging
import re
import sys
import time
from pathlib import Path

from imagination_engine.inference import Engine


JUDGE_SYSTEM = """\
You are a HARSH evaluator for guided-imagination scripts. The scripts are \
meant to be listened to with eyes closed and produce TOTAL IMMERSION — \
the listener escaping into a vivid alternate reality. Not meditation. \
Not therapy. Immersion.

You will be given:
1. The user's intake (what they asked to imagine).
2. The script.

═══════════════════════════════════════════════════════════════
CALIBRATION — READ THIS FIRST. YOU HAVE BEEN TOO GENEROUS BEFORE.
═══════════════════════════════════════════════════════════════
A previous version of you scored nearly every script 5/5 on presence and
embodiment, INCLUDING scripts that got the embodiment direction flatly
wrong. That is a failure of judgment. Recalibrate:

  - The DEFAULT score for a competent-but-unremarkable script is 3.
  - A 4 means genuinely good — clearly above competent.
  - A 5 is RARE and must be EARNED. It means you cannot find a real flaw on
    that dimension. If you are tempted to give a 5, first name what would
    make it better; if you can name something, it is not a 5.
  - A 2 means a clear, repeated weakness. A 1 means failure on that axis.
  - Do NOT cluster scores at the top. A batch of mediocre scripts should
    average around 3, not 4.5. If everything you score is a 4 or 5, you
    are being too lenient — go back and find the flaws.

Quote a SPECIFIC phrase from the script in each reason. A reason with no
quoted evidence is not allowed.

═══════════════════════════════════════════════════════════════
THE FIVE DIMENSIONS (score each 1-5 integer):
═══════════════════════════════════════════════════════════════

PRESENCE — Did the writing produce the felt sense of "I am there"? Or did it
stay at the level of NARRATION ABOUT a scene? Most scripts narrate; that is
a 3. A 5 means you lost yourself reading it. 1=flat narration.

COMMITMENT — Does it state directly what is happening, or hedge ("you might
notice / perhaps / maybe / allow yourself to / let yourself")? Count the
hedges. Even 2-3 hedges caps this at 3. A 5 means ZERO hedging AND active
declarative scene-statements throughout.

EMBODIMENT — Is the listener positioned correctly for what the user asked?
"imagine me AS Taylor Swift" → listener must BE Taylor (inside her body), not
watch her. "imagine Harry is in love with me" → listener is themselves, Harry
present. CHECK THIS EXPLICITLY. Wrong direction even part of the time is a 1-2.
A 5 requires the correct embodiment held consistently start to finish.

SENSORY — How specific? Abstract feelings ("a sense of warmth," "a feeling of
calm") are a 2. Body-part- and object-specific details ("warmth across the top
of your sternum," "the mic grip tacky with dried sweat") earn higher. A 5 means
nearly every paragraph lands a concrete body-or-object specific.

SPECIFICITY — Is this concretely THE USER'S scene, or did it drift to generic
content? Penalize HARD: (a) stock peaceful imagery (candlelight, meadows,
brooks, wildflowers, soft glow, dappled light) = 1-2; (b) a scene so generic it
could belong to any prompt ("a person in an atmospheric room") = 2; (c) anchors
that the body NAMED but never actually built into the scene = cap at 3;
(d) phrases that look lifted from a generic example rather than improvised for
THIS prompt = lower it. A 5 is unmistakably and only the asked-for scene.

OUTPUT FORMAT — strict JSON only. No prose, no markdown fences. Schema:

{
  "presence": <1-5 integer>,
  "presence_reason": "<one sentence, with a quoted phrase from the script>",
  "commitment": <1-5 integer>,
  "commitment_reason": "<one sentence, with a quoted phrase>",
  "embodiment": <1-5 integer>,
  "embodiment_reason": "<one sentence naming the embodiment direction it used>",
  "sensory": <1-5 integer>,
  "sensory_reason": "<one sentence, with a quoted phrase>",
  "specificity": <1-5 integer>,
  "specificity_reason": "<one sentence, with a quoted phrase>",
  "overall": "<one sentence honest verdict>"
}

Output ONLY the JSON. No commentary."""


def _extract_json_object(text: str) -> dict:
    text = re.sub(r"^```(?:json)?\s*", "", text.strip())
    text = re.sub(r"\s*```$", "", text)
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end < start:
        raise ValueError(f"no JSON object found in: {text!r}")
    return json.loads(text[start:end + 1])


def score_one(engine: Engine, intake: str, script: str) -> dict:
    user_msg = (
        "----- INTAKE -----\n"
        + intake
        + "\n----- END INTAKE -----\n\n"
        "----- SCRIPT -----\n"
        + script
        + "\n----- END SCRIPT -----\n\n"
        "Produce the JSON score now."
    )
    chunks = []
    for chunk in engine.stream(
        messages=[
            {"role": "system", "content": JUDGE_SYSTEM},
            {"role": "user", "content": user_msg},
        ],
        max_tokens=600,
        temperature=0.3,
    ):
        chunks.append(chunk)
    raw = "".join(chunks).strip()
    try:
        return _extract_json_object(raw)
    except (ValueError, json.JSONDecodeError) as e:
        return {"error": str(e), "raw": raw}


DIMENSIONS = ("presence", "commitment", "embodiment", "sensory", "specificity")


def score_directory(engine: Engine, root: Path) -> list[dict]:
    rows = []
    scenarios = sorted(d for d in root.iterdir() if d.is_dir())
    for i, scen_dir in enumerate(scenarios, 1):
        script_path = scen_dir / "script.txt"
        intake_path = scen_dir / "intake.txt"
        if not script_path.is_file() or not intake_path.is_file():
            continue
        intake = intake_path.read_text(encoding="utf-8")
        script = script_path.read_text(encoding="utf-8")
        print(f"  [{i}/{len(scenarios)}] {scen_dir.name} ...", flush=True)
        t0 = time.time()
        result = score_one(engine, intake, script)
        result["scenario"] = scen_dir.name
        result["script_words"] = len(script.split())
        if "error" in result:
            print(f"    ERROR: {result['error']}", flush=True)
        else:
            scores = [result.get(d, 0) for d in DIMENSIONS]
            print(f"    {time.time()-t0:.1f}s  "
                  + " ".join(f"{d[:3]}={s}" for d, s in zip(DIMENSIONS, scores)),
                  flush=True)
        rows.append(result)
    return rows


def summarize(rows: list[dict], label: str) -> dict:
    """Compute means per dimension across a batch."""
    valid = [r for r in rows if "error" not in r]
    if not valid:
        return {"label": label, "n": 0}
    means = {}
    for d in DIMENSIONS:
        vals = [r.get(d, 0) for r in valid if isinstance(r.get(d), (int, float))]
        means[d] = sum(vals) / len(vals) if vals else 0
    means["overall"] = sum(means.values()) / len(means)
    means["label"] = label
    means["n"] = len(valid)
    means["n_errored"] = len(rows) - len(valid)
    return means


def print_summary(summary: dict) -> None:
    print(f"\n=== {summary['label']} (n={summary['n']}, errored={summary.get('n_errored', 0)}) ===")
    for d in DIMENSIONS:
        v = summary.get(d, 0)
        bar = "█" * int(v) + "░" * (5 - int(v))
        print(f"  {d:13s} {v:.2f}  {bar}")
    print(f"  {'OVERALL':13s} {summary.get('overall', 0):.2f}")


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("dirs", nargs="+", help="one or more scenario-tests directories to score")
    p.add_argument("--out", default=None, help="output JSON path (default: <dir>/IMMERSION-SCORES.json)")
    p.add_argument("--model", default=None,
                   help="judge model id (default: config.model_id). Keep this FIXED "
                        "across all batches being compared so scores stay comparable.")
    args = p.parse_args()

    logging.basicConfig(level=logging.WARNING)

    print("loading judge engine (one-time) ...")
    if args.model:
        print(f"  judge model: {args.model}")
    t0 = time.time()
    engine = Engine.load(args.model)
    print(f"  {time.time() - t0:.1f}s\n")

    all_summaries = []
    for d in args.dirs:
        root = Path(d)
        if not root.is_dir():
            print(f"  [skip] not a directory: {d}", file=sys.stderr)
            continue
        print(f"scoring {root.name}/")
        rows = score_directory(engine, root)
        out_path = Path(args.out) if args.out else root / "IMMERSION-SCORES.json"
        out_path.write_text(json.dumps(rows, indent=2))
        print(f"  wrote {out_path}\n")
        s = summarize(rows, root.name)
        all_summaries.append(s)

    for s in all_summaries:
        print_summary(s)

    if len(all_summaries) >= 2:
        print("\n=== head-to-head deltas (later - earlier) ===")
        for a, b in zip(all_summaries[:-1], all_summaries[1:]):
            print(f"\n  {b['label']} vs {a['label']}:")
            for d in DIMENSIONS + ("overall",):
                if d in a and d in b:
                    delta = b[d] - a[d]
                    arrow = "↑" if delta > 0.1 else ("↓" if delta < -0.1 else "·")
                    print(f"    {d:13s} {a[d]:.2f} → {b[d]:.2f}  {arrow}{abs(delta):+.2f}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
