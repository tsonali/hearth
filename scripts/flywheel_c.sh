#!/usr/bin/env bash
# One autonomous turn for the COMPANION family: generate honest-mirror candidates ->
# curate -> rebuild training set -> fine-tune -> eval. Tests whether the A-style
# flywheel also lifts C (the other voice family). Self-contained; touches FW_C_DONE.
set -uo pipefail
cd ~/imagination-engine && source .venv/bin/activate
L=~/Downloads/hearth-corpus/_logs; mkdir -p "$L"; rm -f "$L/FW_C_DONE"
say(){ echo "[$(date '+%m-%d %H:%M:%S')] $*" | tee -a "$L/flywheel_c.log"; }

say "1/4 generate companion candidates (3 fresh passes)"
for p in 1 2 3; do HEARTH_GEN_FRESH=1 python scripts/gen_c_candidates.py >> "$L/gen_c.log" 2>&1; done
say "2/4 curate -> c_gold_curated"; python scripts/curate_c.py 2>&1 | tail -1 | tee -a "$L/flywheel_c.log"
say "3/4 rebuild training set"; python scripts/build_training_data.py 2>&1 | tail -2 | tee -a "$L/flywheel_c.log"
say "4/4 fine-tune + eval"
rm -f ~/Downloads/hearth-corpus/_train/adapters/*.safetensors
bash scripts/finetune.sh > "$L/finetune_c.log" 2>&1
tr '\r' '\n' < "$L/finetune_c.log" | grep -iE "Iter [0-9]+:|val loss" | tail -3 | tee -a "$L/flywheel_c.log"
python scripts/test_finetuned.py both > "$L/eval_c.txt" 2>&1
touch "$L/FW_C_DONE"; say "COMPANION FLYWHEEL TURN COMPLETE — eval_c.txt"
