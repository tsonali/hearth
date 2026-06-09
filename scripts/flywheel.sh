#!/usr/bin/env bash
# One full autonomous flywheel turn on the mini: generate more clean A -> promote ->
# taste-cull -> rebuild training set -> fine-tune -> eval. Self-contained (nohup-safe);
# touches FLYWHEEL_DONE at the end. Keeps the mini working with zero babysitting.
set -uo pipefail
cd ~/imagination-engine && source .venv/bin/activate
L=~/Downloads/hearth-corpus/_logs; mkdir -p "$L"; rm -f "$L/FLYWHEEL_DONE"
say(){ echo "[$(date '+%m-%d %H:%M:%S')] $*" | tee -a "$L/flywheel.log"; }

say "1/5 generate clean A -> target ${HEARTH_GEN_TARGET:-600}"
HEARTH_GEN_TARGET=${HEARTH_GEN_TARGET:-600} bash scripts/gen_loop.sh 2>&1 | tail -2 | tee -a "$L/flywheel.log"

say "2/5 promote";    python scripts/promote_a.py 2>&1 | tail -1 | tee -a "$L/flywheel.log"
say "3/5 taste-cull"; python scripts/taste_cull.py 2>&1 | grep -E "KEEP|wrote" | tee -a "$L/flywheel.log"
say "4/5 rebuild";    python scripts/build_training_data.py 2>&1 | tail -2 | tee -a "$L/flywheel.log"

say "5/5 fine-tune + eval"
rm -f ~/Downloads/hearth-corpus/_train/adapters/*.safetensors
bash scripts/finetune.sh > "$L/finetune_fw.log" 2>&1
tr '\r' '\n' < "$L/finetune_fw.log" | grep -iE "Iter [0-9]+:|val loss|out of memory" | tail -3 | tee -a "$L/flywheel.log"
python scripts/test_finetuned.py both > "$L/eval_fw.txt" 2>&1

touch "$L/FLYWHEEL_DONE"
say "FLYWHEEL TURN COMPLETE — eval at eval_fw.txt"
