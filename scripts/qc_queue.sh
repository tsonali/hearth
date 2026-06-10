#!/usr/bin/env bash
# The QC queue-runner — keeps the laptop's single model lane busy FOREVER,
# independent of any Claude session. Runs the battery queue in rotation;
# each pass re-runs everything (the scenario bank samples by date, so each
# day's pass covers a different slice of the usage universe). One model
# process at a time — this is a 16GB machine and that is the law.
#
# Installed as launchd job com.hearth.qcqueue (RunAtLoad + KeepAlive), so it
# survives reboots and crashes. Logs: logs/qc/queue_<timestamp>_<battery>.log
# Claude reads the logs and does the judging whenever a session is alive.
set -uo pipefail
cd "$(dirname "$0")/.." || exit 1
source .venv/bin/activate 2>/dev/null || true
mkdir -p logs/qc

QUEUE=(
  scripts/qc/battery11_imagination_bank.py
  scripts/qc/battery9_engagement.py
  scripts/qc/battery10_registers.py
  scripts/qc/battery2b_honesty.py
  scripts/qc/battery4b_floor.py
  scripts/qc/battery3b_ask_retest.py
  scripts/product_e2e_test.py
)

say() { echo "[$(date '+%m-%d %H:%M:%S')] $*" >> logs/qc/queue.log; }
say "qc-queue runner started (pid $$)"

while true; do
  for b in "${QUEUE[@]}"; do
    # the 16GB rule: never start while another model process lives
    while pgrep -f "battery|product_e2e|gen_._candidates|bench_spec" | grep -v $$ | grep -qv "^$"; do
      sleep 60
    done
    name=$(basename "$b" .py)
    log="logs/qc/queue_$(date +%m%d_%H%M)_${name}.log"
    say "running $name -> $log"
    .venv/bin/python "$b" > "$log" 2>&1
    say "$name exit $? ($(grep -c 'PASS' "$log" 2>/dev/null || echo 0) PASS / $(grep -c 'FAIL' "$log" 2>/dev/null || echo 0) FAIL lines)"
    sleep 120  # let memory settle between model loads
  done
  # once per pass: watchdog the mini's flywheel (sshd has disk access; launchd
  # on either machine can't touch ~/Downloads under TCC). If the trainer
  # stopped — plateau or crash — restart it: each fresh run regrows candidates
  # with the current corpus, so restarts are productive, not spinning.
  if ! ssh -o IdentitiesOnly=yes -o ConnectTimeout=10 smaitra@mac-mini.localdomain       'pgrep -f recursive_flywheel >/dev/null' 2>/dev/null; then
    say "mini flywheel stopped — restarting it"
    ssh -o IdentitiesOnly=yes smaitra@mac-mini.localdomain       'cd ~/imagination-engine && git pull -q origin main; rm -f ~/Downloads/hearth-corpus/_logs/RECURSIVE_DONE; nohup bash scripts/recursive_flywheel.sh > /dev/null 2>&1 & sleep 2; pgrep -f recursive_flywheel >/dev/null && echo restarted'       >> logs/qc/queue.log 2>&1 || say "mini restart FAILED (unreachable?)"
  fi
  say "full pass complete — starting the next (there is no done)"
  sleep 300
done
