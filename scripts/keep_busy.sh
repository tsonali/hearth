#!/usr/bin/env bash
# Never-idle watchdog — SINGLE source of truth for mini generation.
# Lockfile guard: refuses to start if another copy is already running.
cd "$HOME/imagination-engine" || exit 1
export PATH="$HOME/.local/bin:$PATH"
PY=.venv/bin/python
LOG="logs/keep-busy.log"; mkdir -p logs
LOCK="$HOME/imagination-engine/.keepbusy.lock"

# single-instance guard
if [ -f "$LOCK" ] && kill -0 "$(cat "$LOCK" 2>/dev/null)" 2>/dev/null; then
  echo "[keep-busy $(date)] another instance ($(cat $LOCK)) is alive — exiting" >> "$LOG"; exit 0
fi
echo $$ > "$LOCK"
trap 'rm -f "$LOCK"' EXIT
echo "[keep-busy $(date)] watchdog started (pid $$)" >> "$LOG"

while true; do
  if ! pgrep -f run_scenarios.py >/dev/null; then
    sleep 5
    if ! pgrep -f run_scenarios.py >/dev/null; then
      # most recent corpus DIR (not .log) that hasn't been curated yet
      last=$(ls -dt logs/corpus-*/ 2>/dev/null | head -1)
      if [ -n "$last" ] && [ -d "$last" ] && [ ! -f "${last}CURATION.json" ]; then
        echo "[keep-busy $(date)] ${last} finished — curating + cataloging" >> "$LOG"
        $PY scripts/curate_corpus.py "${last%/}" >> "$LOG" 2>&1
        $PY scripts/failure_catalog.py "${last%/}" >> "$LOG" 2>&1
      fi
      next="logs/corpus-auto-$(date +%s)"
      echo "[keep-busy $(date)] launching -> $next" >> "$LOG"
      nohup caffeinate -is $PY scripts/run_scenarios.py \
        --model mlx-community/Qwen2.5-14B-Instruct-4bit \
        --out-dir "$next" --no-voice --verbose >> "${next}.log" 2>&1 &
      sleep 60
    fi
  fi
  sleep 300
done
