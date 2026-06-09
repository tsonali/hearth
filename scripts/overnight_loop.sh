#!/usr/bin/env bash
# Overnight autonomous loop on the mini: finish the generation, fold it in, re-cull,
# rebuild the training set on CURATED data, run the REAL fine-tune, and eval.
# Everything logged; touches REAL_DONE at the end.
set -uo pipefail
cd ~/imagination-engine && source .venv/bin/activate
L=~/Downloads/hearth-corpus/_logs; mkdir -p "$L"; rm -f "$L/REAL_DONE"
say(){ echo "[$(date '+%m-%d %H:%M:%S')] $*" | tee -a "$L/overnight.log"; }

say "waiting for A generation (batch 3) to finish…"
while pgrep -f gen_a_candidates >/dev/null; do sleep 30; done
say "generation done: $(wc -l < ~/Downloads/hearth-corpus/A-imagination/A_generated.jsonl) candidates total"

say "promote -> silver"
python scripts/promote_a.py 2>&1 | tee -a "$L/overnight.log"
say "strict cull -> curated A + C"
python scripts/strict_cull.py 2>&1 | tee -a "$L/overnight.log"
say "rebuild training set (curated)"
python scripts/build_training_data.py 2>&1 | tee -a "$L/overnight.log"

say "clean adapters + run REAL fine-tune"
rm -f ~/Downloads/hearth-corpus/_train/adapters/*.safetensors
bash scripts/finetune.sh > "$L/finetune_real.log" 2>&1
say "fine-tune exit=$?; last lines:"; tr '\r' '\n' < "$L/finetune_real.log" | grep -iE 'Iter [0-9]+:|val loss|out of memory' | tail -4 | tee -a "$L/overnight.log"

say "eval base vs tuned"
python scripts/test_finetuned.py both > "$L/eval_real.txt" 2>&1
say "eval done -> eval_real.txt"

touch "$L/REAL_DONE"
say "OVERNIGHT LOOP COMPLETE"
