#!/usr/bin/env bash
# Keep the mini generating clean A candidates, continuously, until a target pool size.
# Each pass = a fresh variation per intake (temperature -> different script each time),
# clean-anchored + vary-opening per Sonali's taste. Curation (promote/taste_cull) is
# applied after. Stops at TARGET candidates so it doesn't run forever.
set -uo pipefail
cd ~/imagination-engine && source .venv/bin/activate
GEN=~/Downloads/hearth-corpus/A-imagination/A_generated.jsonl
L=~/Downloads/hearth-corpus/_logs
TARGET=${HEARTH_GEN_TARGET:-300}
say(){ echo "[$(date '+%m-%d %H:%M:%S')] $*" | tee -a "$L/genloop.log"; }

for pass in $(seq 1 12); do
  n=$( [ -f "$GEN" ] && wc -l < "$GEN" || echo 0 )
  if [ "$n" -ge "$TARGET" ]; then say "reached target ($n >= $TARGET) — stopping"; break; fi
  say "pass $pass — pool=$n / $TARGET"
  HEARTH_GEN_FRESH=1 python scripts/gen_a_candidates.py >> "$L/gen_a.log" 2>&1 || say "pass $pass errored (continuing)"
done
say "gen loop done; pool=$( [ -f "$GEN" ] && wc -l < "$GEN" || echo 0 )"
