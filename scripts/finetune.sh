#!/usr/bin/env bash
# Hearth fine-tune — LoRA on Qwen 2.5 14B (4-bit) with MLX, LOCAL on the mini.
# On-thesis: training runs on our own machine, nothing leaves the house, $0.
# Falls back to a cloud GPU only if 16GB can't hold it (see own-model-plan.md).
#
# Data: ~/Downloads/hearth-corpus/_train/{train,valid}.jsonl  (built by build_training_data.py)
# Output adapters: ~/Downloads/hearth-corpus/_train/adapters/
set -euo pipefail
cd ~/imagination-engine && source .venv/bin/activate

MODEL="mlx-community/Qwen2.5-14B-Instruct-4bit"
DATA="$HOME/Downloads/hearth-corpus/_train"
ADAPTERS="$DATA/adapters"
mkdir -p "$ADAPTERS"

# Conservative config to fit 14B-4bit LoRA in 16GB unified memory:
#   - tune only the top layers (--num-layers 8), batch 1, capped sequence length.
# If it OOMs: drop --num-layers to 4, --max-seq-length to 1024, or switch MODEL to
# mlx-community/Qwen2.5-7B-Instruct-4bit to validate the pipeline first.
# OOM fix (iter-100 crash was the val pass blowing past 16GB): shorter sequences are
# the biggest memory lever, fewer tuned layers, smaller + less frequent validation.
python -m mlx_lm lora \
  --model "$MODEL" \
  --train \
  --data "$DATA" \
  --fine-tune-type lora \
  --num-layers 6 \
  --batch-size 1 \
  --max-seq-length 1024 \
  --iters 1500 \
  --learning-rate 1e-5 \
  --steps-per-report 25 \
  --steps-per-eval 300 \
  --val-batches 8 \
  --save-every 200 \
  --adapter-path "$ADAPTERS"

echo "done — adapters in $ADAPTERS"
echo "test with:  python -m mlx_lm generate --model $MODEL --adapter-path $ADAPTERS --prompt '...'"
