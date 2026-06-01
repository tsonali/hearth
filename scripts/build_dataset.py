"""Build the JSONL fine-tuning dataset from curated KEEPER scripts.

Pipeline step 4. Reads a corpus dir + its CURATION.json, takes only the keepers,
and emits training pairs (intake/instruction → the script) as JSONL — the format
MLX-LM / TRL / Unsloth consume. This dataset is itself a CC0 artifact worth
publishing (the access-native thesis: even the training data is free + clean).

    .venv/bin/python scripts/build_dataset.py logs/corpus-v6_2 --out data/train/imagination.jsonl

Each line is a chat-format record:
  {"messages": [{"role":"system","content": <protocol>},
                {"role":"user","content": <intake transcript>},
                {"role":"assistant","content": <the guided script>}]}

We train the model to map (system protocol + user's intake) → a great script.
Provenance is logged per record so the dataset is auditable.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

SYSTEM = (
    "You are the Imagination Engine. Given a short intake conversation about what "
    "the user wants to imagine, write a single continuous guided-imagination script: "
    "an opening that drops them into the scene, a body that moves through it with "
    "fresh sensory detail at each step (never repeating), and a gentle return. "
    "Second person, present tense, committed, immersive. Plain text, blank lines "
    "between paragraphs."
)


def read_intake(intake_path: Path) -> str:
    """Flatten an intake.txt ([USER]/[ENGINE] blocks) into a clean transcript."""
    if not intake_path.is_file():
        return ""
    raw = intake_path.read_text(encoding="utf-8")
    # Normalize the [USER]/[ENGINE] markers into a readable transcript.
    raw = raw.replace("[USER]", "User:").replace("[ENGINE]", "Engine:")
    return re.sub(r"\n{3,}", "\n\n", raw).strip()


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("dir", help="corpus directory containing CURATION.json")
    p.add_argument("--out", required=True, help="output .jsonl path")
    p.add_argument("--include-all", action="store_true",
                   help="ignore curation, include every script (NOT recommended)")
    args = p.parse_args()
    root = Path(args.dir)
    cur_path = root / "CURATION.json"

    if args.include_all:
        keep_ids = {d.name for d in root.iterdir() if (d / "script.txt").is_file()}
    else:
        if not cur_path.is_file():
            print(f"no CURATION.json in {root} — run curate_corpus.py first "
                  f"(or pass --include-all)", file=sys.stderr)
            return 1
        cur = json.loads(cur_path.read_text())
        keep_ids = {r["id"] for r in cur["scripts"] if r["keep"]}

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    n = 0
    skipped = 0
    with out_path.open("w", encoding="utf-8") as f:
        for d in sorted(p for p in root.iterdir() if p.is_dir()):
            if d.name not in keep_ids:
                continue
            script = (d / "script.txt")
            if not script.is_file():
                continue
            intake = read_intake(d / "intake.txt")
            if not intake:
                # fall back to the scenario prompt if intake.txt missing
                sj = d / "scenario.json"
                if sj.is_file():
                    intake = "User: " + json.loads(sj.read_text()).get("prompt", "")
            if not intake:
                skipped += 1
                continue
            record = {
                "messages": [
                    {"role": "system", "content": SYSTEM},
                    {"role": "user", "content": intake},
                    {"role": "assistant", "content": script.read_text(encoding="utf-8").strip()},
                ],
                "meta": {"source": d.name},
            }
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
            n += 1

    print(f"=== dataset built ===")
    print(f"  source: {root}  ({'ALL scripts' if args.include_all else 'curated keepers'})")
    print(f"  wrote {n} training pairs → {out_path}" + (f"  (skipped {skipped} w/o intake)" if skipped else ""))
    if n < 50:
        print(f"  NOTE: {n} examples is light — a narrow LoRA wants ~500-1000+ clean "
              f"pairs. Generate/curate more before the real fine-tune.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
