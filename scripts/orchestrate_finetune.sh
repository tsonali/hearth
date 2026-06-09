#!/usr/bin/env bash
# Full autonomous chain on the mini: wait for generation -> promote -> rebuild ->
# LoRA fine-tune -> base-vs-tuned eval. Logs everything; touches DONE at the end.
set -uo pipefail
cd ~/imagination-engine && source .venv/bin/activate
L=~/Downloads/hearth-corpus/_logs
mkdir -p "$L"; rm -f "$L/PIPELINE_DONE"
say(){ echo "[$(date +%H:%M:%S)] $*" | tee -a "$L/pipeline.log"; }

say "waiting for A generation to finish…"
while pgrep -f gen_a_candidates >/dev/null; do sleep 30; done
say "generation done."

say "promoting concrete candidates -> silver"
python scripts/promote_a.py 2>&1 | tee -a "$L/pipeline.log"

say "rebuilding training set"
python scripts/build_training_data.py 2>&1 | tee -a "$L/pipeline.log"

say "starting LoRA fine-tune (this is the long part)…"
bash scripts/finetune.sh > "$L/finetune.log" 2>&1
say "fine-tune exit=$? (see finetune.log tail:)"; tail -5 "$L/finetune.log" | tee -a "$L/pipeline.log"

say "running base-vs-tuned eval"
python scripts/test_finetuned.py both > "$L/eval.txt" 2>&1
say "eval done -> eval.txt"

touch "$L/PIPELINE_DONE"
say "PIPELINE COMPLETE"
