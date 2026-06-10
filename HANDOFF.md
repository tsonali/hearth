# HANDOFF — resume here (read this first)

_Last updated mid-session, 2026-06-09. This file is the single source of truth for a
fresh session to pick up EXACTLY where we left off. Everything below is real and
running; nothing here depends on the previous chat staying alive._

## FIRST THING TO DO when you resume — run these checks
```bash
# Mini = the always-on grind/train box. These survive any chat restart (nohup + caffeinate).
ssh -o IdentitiesOnly=yes smaitra@mac-mini.localdomain '
  echo "trainer: $(pgrep -f recursive_flywheel >/dev/null && echo RUNNING || echo stopped)"
  echo "caffeinate: $(pgrep -x caffeinate >/dev/null && echo ON || echo OFF)"
  echo "best val loss: $(cat ~/Downloads/hearth-corpus/_train/best_adapters/best_loss.txt)"
  tail -12 ~/Downloads/hearth-corpus/_logs/recursive.log'
# If trainer stopped and not at plateau: cd ~/imagination-engine && nohup bash scripts/recursive_flywheel.sh &
# If caffeinate OFF: nohup caffeinate -dimsu >/dev/null 2>&1 &   (on BOTH mini and laptop)
```

## WHERE WE ARE
Hearth is a **functionally complete, working v0** — all four tools run end-to-end on
**our own fine-tuned model** (not base Qwen), and it's installable + public.
- Tools (all QC'd through the real model, weak spots fixed): Imagination (immersion+settling
  fork), Secretary, Companion (smart/non-prescriptive), Build-Your-Own, Ask-Your-Files.
- Own model: local MLX LoRA on Qwen2.5-14B-4bit; **best val loss 1.193**; adapter wired into
  the product (`Engine.load` reads `config.adapter_path` = `data/model/adapters`).
- Voice: 3 voices (Chatterbox her/him + F5 own) + one-button **voice trainer** (`/record`).
- Install: `Start Hearth.command` (double-click) + `Hearth.app` + `scripts/package.sh`
  → `dist/hearth-<ver>.zip`. Public repo: github.com/tsonali/hearth (main).

## WHAT'S RUNNING (autonomous, survives restart)
- **Mini:** `recursive_flywheel.sh` — alternates A/C generate→curate→retrain, keeps the BEST
  adapter (`_train/best_adapters/`), stops at plateau. Logs: `_logs/recursive.log`.
- **caffeinate ON** mini + laptop (don't sleep).

## LATEST QC PASS (2026-06-09, evening — all five tools re-read through the real model)
Companion + Imagination intake passed clean. Three weak spots found and FIXED (prompt
layer, verified by re-run): Ask-Your-Files no longer rambles or cites in-text (UI shows
sources); Build-Your-Own personas can't open with assistant hedges ("I think…");
Secretary firm drafts keep a real email frame ([Landlord's Name] / [Your name]).
Also: NO sqlite ships anymore — all per-user stores untracked + blanket-ignored +
stripped/audited in package.sh (zip went 15MB→5.3MB). The old committed ask.sqlite held
only public-domain Gutenberg test text — no private leak, no history rewrite needed.

## NEXT ACTIONS (the autonomous loop — keep going without asking)
1. When the trainer beats 1.193, pull the best adapter to the product + re-QC:
   `scp 'smaitra@mac-mini.localdomain:~/Downloads/hearth-corpus/_train/best_adapters/*.safetensors' data/model/adapters/`
   then `.venv/bin/python scripts/product_e2e_test.py` and read all 4 tools honestly.
2. Build → test → fix loop: run `scripts/product_e2e_test.py`, fix any tool that feels
   AI-y / off, commit, repeat. (The bar: "would I actually send/keep/believe this.")
3. Keep committing to `main` and pushing (public). **Never** commit: the corpus, voice
   wavs, checkpoints, `data/model/adapters`, `docs/internal/` (all gitignored — keep it so).

## TWO THINGS GATED ON SONALI (not skipped)
- **Notarized `.dmg`** — needs her Apple Developer account ($99). Unsigned app works today.
- **F5 own-voice speed vs quality** — needs her ear to pick the tradeoff.

## DO NOT
- Do not publish `docs/internal/why-public-domain.md` (pending her review — see task).
- Do not put any cloud model (Claude/Fable/GPT) IN the product — local only. (Fine to
  *build with* a frontier model; never ship one.)
- Do not distill from non-permissive models (keep the own-model's Qwen/Apache lineage clean).

## WORKING STYLE (her explicit direction)
Act autonomously, don't over-ask, be brutally honest about quality, test test test, keep
the mini busy. She drives; Claude builds.
