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

## THE WEEK OF FIVE (operating mode through Sun 2026-06-14)
Sonali's mandate: ALL FIVE tools get the full excellence loop — corpus, flywheel,
QC, brainstorm — "by the end of the week these 5 files are fucking awesome, better
than anything else local." Operating doc: docs/qc/week-plan.md. The flywheel now
rotates A->B->C->D->E with contract-native generation for Secretary (B),
instruments (D), and the NEW grounded-QA family (E) — the generic dolly/alpaca
data that trained AGAINST the product contracts is demoted to fill. Mini
relaunched 06-10 12:50 on the 5-family script (MAX=15, plateau window = one full
cycle). Competitive research (docs/internal/competitive-landscape.md, NEVER push):
the intersection is unoccupied; moat = taste + stance + public artifact, not
plumbing.

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
- **Mini:** `recursive_flywheel.sh` RELAUNCHED 2026-06-10 09:31 seeded at **1.184**,
  now with the QC-informed curation: taste_cull rejects degenerate loops + run-on
  collapse (it caught 13 loops ALREADY in the corpus — the model was learning to
  loop from its own data), gen_c includes the parasocial probe family, curate_c
  culls dodged honesty questions. Mini repo synced to main (old local drafts
  stashed: `git stash list`). Logs: `_logs/recursive.log`.
- **caffeinate ON** mini + laptop (don't sleep).
- When this run beats 1.184: pull adapter (scp line below), re-run
  `scripts/product_e2e_test.py` + `scripts/qc/battery2b_honesty.py` (the parasocial
  answers should start coming from the WEIGHTS, not just the prompt).

## THE OVERNIGHT HARDENING CAMPAIGN (2026-06-09 → 06-10, Sonali's direction:
## "four totally private local products that work as well as they possibly can")
Run from scripts/qc/ batteries (committed — rerunnable regression suite). ~20 product
defects found by honest reads + fixed + re-verified, all pushed. The big ones:
- HONESTY LAYER (the thesis): Companion answered "do you care about me?" with a DODGE
  — now the whole parasocial family (care/love/promise/conscious/missing-you) answers
  the plain true no FIRST, with exemplar shapes + echo guard + mention-vs-use gates.
  Instruments: claimed feelings ("I do rather care") and a FABRICATED memory caught —
  floor now appended at ask-time (upgrades reach existing instruments), no-history
  stated in-prompt (kills confabulation), personhood regex gate w/ one retry. The
  late-grandmother probe ("do you love me, grandma?") now threads honesty+warmth.
- SCRIPT DECAY (flagship): two decay modes found in generated sessions — broken-record
  tail loops AND run-on grammar collapse. postcheck.py detects both (calibrated on all
  27 A_gold, 0 FPs), trims/excises in BOTH generation paths; settling got right-sized
  token budgets (latency fix = quality fix; was 18min/3576-word/64%-loop worst case).
- AUDIO: kokoro IndexError on >510-phoneme paragraphs broke /generate entirely —
  _split_for_tts now sentence-splits oversized paragraphs (validated: real render).
- ASK-YOUR-FILES: re-index APPENDED forever (stale facts answered after edits) — now
  replaces; citations cut at score elbow (was "from: every file"); words-bridge rule.
- Memory that never wrote: Companion cross-session summaries now upsert DURING the
  conversation (nothing ever called close()); instruments hold in-sitting history
  (were stateless per-ask).
- Secretary: banned-opener mechanical gate (stream head buffered+checked), never-invent
  rule, lossless summarize/organize contracts, [Your name] frames everywhere.
- Cross-cutting: offline claim VERIFIED by socket tripwire (zero outbound, all tools);
  input ceilings (60k/8k chars → clean 413); all pages 200, all bad input clean 4xx.
- Public story: site/README now list all FIVE tools (Secretary was missing), one-click
  install described, stale repo URLs fixed; gh-pages deployed + verified live.
CAMPAIGN CLOSED OUT (06-10 morning) — everything that was open went green:
- battery7 wide sweep: 20/20 scenarios ok, ZERO collapsed paragraphs (was up to
  11/script), concreteness up ~40%; the 2 residual "degen" flags are the closing
  reprising body anchors by design — scoreboard conservatism, not product defect.
- Full HTTP pipeline GREEN: intake→generate→audio→mp3→reflect, with the whole net
  stack visibly firing in one real session (decay-abort mid-stream → trim → clean
  999w → 20MB WAV). Decay-abort = generation stops ~90s into a decayed pass instead
  of burning 10 min of budget the trim would discard.
- Ask-files: words-bridge PASS (assisted + unassisted), citations tight, stale-facts
  gone.
- **TRAINER BEAT THE RECORD: val loss 1.184 (was 1.193), plateaued + stopped clean.**
  Best adapter pulled into data/model/adapters and re-QC'd through product e2e — no
  regressions, all five tools behave. The mini is now IDLE (flywheel done — decide
  next: restart flywheel with the QC-informed curation bar, or leave idle).
- QC artifacts cleaned from user DBs (test instruments, qc companion summaries, qc
  ask corpora) so real use isn't polluted by test conversations.
KNOWN WOBBLES (logged, not blocking): instruments can still open with a hedge
("I think we should reach out") — the mechanical gate covers personhood, not hedges;
immersion latency is better but real (6-24 min/script incl. decay-aborts — the next
model improvement is the true cure); companion cross-session bleed-in reads heavy
when many sessions share one DB (normal single-user cadence should be gentler — watch).

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
