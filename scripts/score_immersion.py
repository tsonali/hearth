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
You are an evaluator for guided-imagination scripts. The scripts are \
meant to be listened to with eyes closed and produce TOTAL IMMERSION — \
the listener escaping into a vivid alternate reality. Not meditation. \
Not therapy. Immersion.

You will be given:
1. The user's intake (what they asked to imagine).
2. The script.

You score five dimensions on 1-5 (5 = best):

PRESENCE — Did the writing produce the felt sense of "I am there" while you read it? Or did it stay at the level of narration about a scene? 1=flat narration. 5=full transport.

COMMITMENT — Does the script state directly what is happening in the scene, or hedge with "you might notice / perhaps / maybe / allow yourself to"? 1=meditation-app hedging throughout. 5=direct committed prose throughout.

EMBODIMENT — Is the listener positioned correctly given what the user asked for? If they said "imagine me as Taylor Swift," is the listener IN Taylor's body, or watching Taylor? If they said "imagine Harry Styles is in love with me," is the listener themselves with Harry present, or somewhere wrong? 1=completely wrong subject/position. 5=exactly right embodiment direction throughout.

SENSORY — How specific are the sensory details? Abstract feelings ("a sense of warmth") score low. Body-part-specific and object-noun-specific details ("warmth across the top of your sternum," "the mic grip has a faint tackiness from dried sweat") score high. 1=abstractions throughout. 5=concrete body-part / object specifics throughout.

SPECIFICITY — Is the script specifically about THE SCENE THE USER ASKED FOR, or did it retreat to stock peaceful imagery (candlelight, meadows, brooks, wildflowers, soft glow, dappled light)? 1=generic peaceful meditation content unrelated to the prompt. 5=specifically and concretely the asked-for scene throughout.

OUTPUT FORMAT — strict JSON only. No prose, no markdown fences. Schema:

{
  "presence": <1-5 integer>,
  "presence_reason": "<one sentence>",
  "commitment": <1-5 integer>,
  "commitment_reason": "<one sentence>",
  "embodiment": <1-5 integer>,
  "embodiment_reason": "<one sentence>",
  "sensory": <1-5 integer>,
  "sensory_reason": "<one sentence>",
  "specificity": <1-5 integer>,
  "specificity_reason": "<one sentence>",
  "overall": "<one sentence honest verdict>"
}

Be strict. A 5 means it's genuinely excellent on that dimension. A 3 is middling. A 1 is a clear failure. Don't be generous.

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
    args = p.parse_args()

    logging.basicConfig(level=logging.WARNING)

    print("loading engine (one-time) ...")
    t0 = time.time()
    engine = Engine.load()
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
