#!/usr/bin/env bash
# Recursive flywheel: keep improving the model all night. Each turn alternates
# growing A (imagination) and C (companion) with fresh curated data, retrains,
# and tracks val loss. Saves the BEST adapter seen. Stops when val loss stops
# improving for 2 turns (true plateau) or after MAX turns. Self-contained / nohup.
set -uo pipefail
cd ~/imagination-engine && source .venv/bin/activate
L=~/Downloads/hearth-corpus/_logs; mkdir -p "$L"; rm -f "$L/RECURSIVE_DONE"
BEST=~/Downloads/hearth-corpus/_train/best_adapters; mkdir -p "$BEST"
ADAP=~/Downloads/hearth-corpus/_train/adapters
say(){ echo "[$(date '+%m-%d %H:%M:%S')] $*" | tee -a "$L/recursive.log"; }

MAX=${HEARTH_MAX_TURNS:-8}
best_loss=$(cat "$BEST/best_loss.txt" 2>/dev/null || echo 1.193)   # seed w/ current best
no_improve=0
say "recursive flywheel start — MAX=$MAX, seed best_loss=$best_loss"

for turn in $(seq 1 "$MAX"); do
  if [ $((turn % 2)) -eq 1 ]; then
    say "turn $turn — grow A (imagination)"
    HEARTH_GEN_FRESH=1 python scripts/gen_a_candidates.py >> "$L/gen_a.log" 2>&1 || true
    python scripts/promote_a.py >> "$L/recursive.log" 2>&1 || true
    python scripts/taste_cull.py >> "$L/recursive.log" 2>&1 || true
  else
    say "turn $turn — grow C (companion)"
    HEARTH_GEN_FRESH=1 python scripts/gen_c_candidates.py >> "$L/gen_c.log" 2>&1 || true
    python scripts/curate_c.py >> "$L/recursive.log" 2>&1 || true
  fi

  python scripts/build_training_data.py >> "$L/recursive.log" 2>&1 || true
  rm -f "$ADAP"/*.safetensors
  bash scripts/finetune.sh > "$L/finetune_rec.log" 2>&1 || { say "turn $turn train FAILED"; continue; }

  loss=$(tr '\r' '\n' < "$L/finetune_rec.log" | grep -iE "Val loss" | tail -1 | grep -oE '[0-9]+\.[0-9]+' | head -1)
  loss=${loss:-9.99}
  say "turn $turn — val loss $loss (best $best_loss)"

  improved=$(python3 -c "print(1 if float('$loss') < float('$best_loss') - 0.005 else 0)")
  if [ "$improved" = "1" ]; then
    best_loss=$loss; no_improve=0
    cp -f "$ADAP"/*.safetensors "$BEST"/ 2>/dev/null
    echo "$best_loss" > "$BEST/best_loss.txt"
    python scripts/test_finetuned.py both > "$L/eval_best.txt" 2>&1 || true
    say "turn $turn — NEW BEST ($best_loss) — adapter saved, eval -> eval_best.txt"
  else
    no_improve=$((no_improve+1))
    say "turn $turn — no improvement ($no_improve/2)"
    [ "$no_improve" -ge 2 ] && { say "PLATEAU — stopping"; break; }
  fi
done

touch "$L/RECURSIVE_DONE"
say "RECURSIVE FLYWHEEL DONE — best val loss $best_loss (best adapter in best_adapters/)"
