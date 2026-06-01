# Building our own model — the distillation pipeline

The goal: **a guided-imagination specialist model that is all our own** — distilled
from an Apache-2.0 teacher (Qwen) onto data we control, then dedicated CC0. The
result owes nothing to anyone: weights aren't copyrightable (no human authorship),
and the Apache license affirmatively grants the right to distill + relicense. This
is the access-native thesis made into an artifact. (See decisions-log 2026-05-29.)

## What we are NOT doing
- **NOT training an LLM from scratch.** That's thousands of GPU-years + a
  multi-trillion-token dataset + a large team + $10M+. Out of scope, forever (for
  the general base). We stand on a permissively-licensed base instead.

## What we ARE doing: distill a specialist
A task-tuned small model can match or beat a frontier generalist *on its niche*
(LoRA Land, clinical-extraction evidence). We fine-tune/distill Qwen into a model
specialized for one task (guided-imagination scripts) that runs locally, free.

## The pipeline (data first — most of it is buildable NOW, no grind box)

**Stage 1 — Generate a corpus (now, laptop/grind box).**
Use Qwen + scene-binding to produce many sessions across all archetypes/scenarios.
DATA QUALITY IS EVERYTHING — a fine-tune learns whatever we feed it, flaws included.
→ This is why the generator-quality fixes (kill repetition/looping) are STEP ONE of
building the model, not a side quest: looping scripts = a model that learns to loop.

**Stage 2 — Curate ruthlessly (now).**
Score every generated script (mechanical floor + immersion rubric + Claude read);
keep only the genuinely excellent. Quality > quantity: ~500–1,000 clean examples
beat 5,000 noisy ones (LIMA result). Toss anything that drifts, loops, or hedges.

**Stage 3 — Format as training pairs (now).**
Convert kept sessions to JSONL (intake transcript → great script), the format
TRL/Unsloth/MLX-LM consume. This is our dataset — itself a CC0 artifact worth
publishing.

**Stage 4 — Fine-tune (later, grind box).**
LoRA/QLoRA on Qwen via MLX-LM (Apple Silicon) or Unsloth (rented GPU, <$20, hours).
QLoRA r=16/alpha=32/lr=2e-4 as a starting recipe. Produces a small adapter (~tens-
hundreds of MB) on the shared base.

**Stage 5 — Evaluate head-to-head (later).**
Specialist vs. off-the-shelf-Qwen+scaffolding on the rubric + Claude reads +
mechanical floor. Does it drift less? Need less scaffolding? Read more immersive?

**Stage 6 — Maximal version (north star).**
Train from scratch on PUBLIC-DOMAIN data only (LibriVox audio = PD; PD/CC0 text) —
drops even the teacher. The purest "owes nothing to anyone" artifact. Big effort;
hold as the statement-making endgame.

## Honest dependencies & risks
- Distilling subjective *creative quality* (immersion) is less proven than distilling
  verifiable tasks (math/extraction). A real research bet — validate empirically,
  don't assume.
- Heavy generation + the fine-tune itself want the grind box; dataset curation +
  formatting do not.
- Teacher MUST be Apache/MIT (Qwen/Mistral/DeepSeek). Never Llama/Gemma≤v3/frontier
  (contract strings). Qwen base = already clean.

## Immediate next step
Fix the generator so its output is training-grade (no looping/repetition), then
generate + curate the first clean batch. That batch IS the seed of our own model.
