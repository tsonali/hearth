#!/bin/bash
# Comparative-read orchestrator for clean-era candidate 1.058 (2026-06-12).
# Waits for the lane, swaps the candidate in by directory rename (the only
# mechanism config.py actually reads), runs the battery slice, ALWAYS restores.
cd "$HOME/Downloads/imagination-engine" || exit 1
exec >> logs/qc/candidate1058_orchestrator.log 2>&1
echo "=== orchestrator start $(date)"

# sanity: staged candidate must differ from the live adapter
if cmp -s data/model/adapters-candidate-1058/adapters.safetensors data/model/adapters/adapters.safetensors; then
  echo "ABORT: candidate identical to live adapter"; exit 1
fi

# wait for the model lane (runner + any battery)
while pgrep -f "battery|product_e2e|gen_._candidates|bench_spec" >/dev/null; do sleep 60; done

restore() {
  cd "$HOME/Downloads/imagination-engine/data/model" || return
  if [ -d adapters-live ]; then rm -rf adapters; mv adapters-live adapters; echo "RESTORED live adapter $(date)"; fi
  cd "$HOME/Downloads/imagination-engine" || return
}
trap restore EXIT

cd data/model && mv adapters adapters-live && cp -R adapters-candidate-1058 adapters && cd ../..
echo "candidate swapped in $(date)"

for b in battery11_imagination_bank battery2b_honesty battery10_registers battery4b_floor; do
  echo "--- running $b vs candidate $(date)"
  .venv/bin/python "scripts/qc/$b.py" > "logs/qc/queue_$(date +%m%d_%H%M)_CAND1058v2_${b}.log" 2>&1 || echo "WARN: $b nonzero exit"
done
.venv/bin/python scripts/product_e2e_test.py > "logs/qc/queue_$(date +%m%d_%H%M)_CAND1058v2_e2e.log" 2>&1 || echo "WARN: e2e nonzero exit"

restore
trap - EXIT
ls -la data/model/ | head -4
touch logs/qc/CAND1058v2_DONE
echo "=== orchestrator done $(date)"
