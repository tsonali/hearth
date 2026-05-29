#!/usr/bin/env bash
#
# morning_report.sh — the local half of the "daily grind" morning report.
#
# Turns whatever scenario-test batches exist into a scored, analyzed,
# dated report you can read with coffee. Runs entirely on this Mac; needs
# no network and no remote scheduler. The remote Claude routine (when its
# service is up) adds the judgment layer on top of this; this script is
# the muscle + the numbers.
#
# What it does, in order:
#   1. SCORE   — strict-rubric LLM judge over every logs/scenario-tests-* dir
#                (one FIXED judge model so scores stay comparable; default
#                Llama 3.1 8B). Writes a head-to-head delta table.
#   2. ANALYZE — the ungameable mechanical floor (hedges, stock imagery,
#                prompt-engagement, short scripts) per batch.
#   3. REPORT  — tees everything to logs/reports/<date>.md so it persists.
#
# Usage:
#   bash scripts/morning_report.sh                 # score+analyze all batches
#   bash scripts/morning_report.sh --judge MODEL   # override the judge model
#
# NOTE: uses .venv/bin/python directly. `uv run` currently re-resolves deps
# and fails on a chatterbox/diffusers pin conflict — the venv already has
# everything installed, so we call its python straight.

set -euo pipefail
cd "$(dirname "$0")/.."

JUDGE=""
if [[ "${1:-}" == "--judge" && -n "${2:-}" ]]; then
  JUDGE="--model $2"
fi

PY=.venv/bin/python
STAMP="$(date +%Y-%m-%d)"
REPORT_DIR="logs/reports"
REPORT="$REPORT_DIR/${STAMP}.md"
mkdir -p "$REPORT_DIR"

# Every batch that actually has generated scripts in it.
BATCHES=()
for d in logs/scenario-tests*; do
  [[ -d "$d" ]] || continue
  if compgen -G "$d/*/script.txt" > /dev/null; then
    BATCHES+=("$d")
  fi
done

{
  echo "# Morning report — ${STAMP}"
  echo
  if [[ ${#BATCHES[@]} -eq 0 ]]; then
    echo "No scenario-test batches with scripts found. Nothing to score yet."
    exit 0
  fi
  echo "Batches scored: ${BATCHES[*]}"
  echo "Judge: ${JUDGE:-default (config.model_id)}  — kept FIXED across batches for comparability."
  echo
  echo '## Immersion scores (strict rubric v2) + head-to-head deltas'
  echo '```'
} | tee "$REPORT"

# 1. SCORE — all batches in one call so the script prints the delta table.
$PY scripts/score_immersion.py "${BATCHES[@]}" $JUDGE 2>&1 | tee -a "$REPORT"

{
  echo '```'
  echo
  echo '## Mechanical floor (no judge — ungameable)'
} | tee -a "$REPORT"

# 2. ANALYZE — mechanical metrics per batch.
for d in "${BATCHES[@]}"; do
  {
    echo
    echo "### $d"
    echo '```'
  } | tee -a "$REPORT"
  $PY scripts/analyze_v2_scripts.py "$d" 2>&1 | tee -a "$REPORT"
  echo '```' | tee -a "$REPORT"
done

echo | tee -a "$REPORT"
echo "Report written: $REPORT" | tee -a "$REPORT"
echo "Next: curate the highlights + decision queue into docs/daily-log.md."
