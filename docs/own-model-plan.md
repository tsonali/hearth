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

## Making it OURS — the full arsenal (not just fine-tuning data)

Fine-tuning data is one lever. The real "make it our own, over many nights on the
mini" program STACKS several methods. Ranked by leverage-for-effort:

**TIER 1 — high-leverage, the multi-night program:**
- **(a) Continued pre-training on a domain corpus.** Keep pre-training Qwen on a
  big pile of raw in-domain text (guided-imagery scripts, meditation transcripts,
  evocative sensory prose, public-domain literature) BEFORE task tuning. Shifts the
  model's whole *register/feel* toward our world at a deeper level than task tuning.
  Compute-hungry → ideal mini overnight job.
- **(b) Task fine-tuning (LoRA/QLoRA)** on curated intake→script pairs. Teaches the
  task. Iterative: generate → curate → tune → find weak spots → generate TARGETED
  data for them → retune. The dataset is a living thing grown over rounds.
- **(c) Preference tuning (DPO) — the TASTE injector.** Show the model PAIRS
  ("this script is better than that one," from Sonali's taste + the immersion
  rubric). It learns our *preferences*, not just imitation — the competent→moving
  gap. Clean mini job; the right tool (not full RLHF).
- **(d) Iterate (a)/(b)/(c) over many rounds**, each cycle targeting the prior
  round's measured weaknesses. This IS "train it extensively over many nights."

**TIER 2 — real, narrower:**
- **(e) Model merging** (mergekit): train per-archetype/per-task specialists, merge
  into one. Cheap, sometimes shockingly good. For when we have several packs.
- **(f) Self-improvement loop:** model generates → rubric/judge scores → best
  outputs become next round's training data. Powerful but needs a TRUSTWORTHY judge
  (we have rubric + mechanical floor); can amplify flaws if the judge is weak.

**TIER 3 — traps, do NOT pursue:** train-from-scratch (GPU-years); architecture
surgery (huge effort, tiny payoff, high risk); full RLHF (DPO gets ~the benefit far
cheaper).

**The maximal statement (north star):** redo (a) on PUBLIC-DOMAIN-ONLY data so even
the pre-training corpus is clean → a model that is ours and no one else's, all the
way down.

**Order matters, and DATA QUALITY GATES EVERYTHING.** Every technique above
amplifies whatever the data quality is — garbage corpus → garbage at every stage.
So the unglamorous current step (generator producing clean, non-looping,
genuinely-good scripts) is the foundation the entire program stands on. We earn the
multi-night training program by first making the data worth training on.

## The use-case families (what we train on) — A, B, C, all in, however long it takes

We do NOT train one do-everything model. The task-pack architecture = shared base +
per-FAMILY specialist adapters, because the families want OPPOSITE tuning targets
(dreamy-evocative vs. faithful-restrained) and can't be maxed in one set of weights.

**Family A — Immersive / experiential (the dreamy; Sonali's wheelhouse; flagship).**
Guided imagination (built), meditation/wind-down/sleep, **Unreality / dream
sequences** (the thesis made playable), **immersive in-world / lore / "instruction-
manual-as-fiction"** worldbuilding. Tuning target: sensory specificity, commitment,
immersion, evocative register.

**Family B — Reliable text utility (the broad public draw).** Writing transformer
(rewrite/summarize/translate/tone), doc-Q&A over your own files (RAG), structured
extraction. Tuning target: faithfulness, restraint, don't-embellish, structure —
the OPPOSITE of A. (Commoditized but it's what makes the tool a daily utility.)

**Family C — Reflective / interactive: an honest, private, modern ELIZA.**
Structured journaling/reflection, rehearsal, decision-thinking. **The key insight
(Sonali, via Weizenbaum's ELIZA, 1966):** ELIZA's value was never intelligence — it
was being a PRIVATE, NON-JUDGING MIRROR that reflected the person back to themselves;
the human did the real work. This maps perfectly onto (a) what a small local model
can actually do — reflection = structured transformation of the user's OWN words,
needs zero frontier IQ (small models lose at SUPPLYING empathy, fine at mirroring);
and (b) the instrument-not-companion thesis. Crucially, a modern ELIZA that is
HONEST about being a mirror is ELIZA done the way Weizenbaum (who was horrified
people mistook the mirror for a mind) wished it had been — Sonali's thesis as the
answer to his fear. This is the thesis in interactive form, not just a utility mode.
  Design discipline (keeps it honest AND within a small local model's real ability):
  reflect-don't-advise (transform, never dispense wisdom); brevity (ELIZA was one
  line — kills rambling-affirmation); honest frame up front ("a private mirror, not
  a person, not a therapist; nothing leaves this machine; here to help you hear
  yourself"); crisis honesty (point to real humans at its limits — non-negotiable).

**Sequencing (Sonali: get it right, take the time):** train Family A first (flagship,
soul, already in motion, where "dreamy" lives) → then C (the ELIZA-mirror, the
frontier/statement piece) and B (the reach/utility). All three, no rush.

## Honest dependencies & risks
- Distilling subjective *creative quality* (immersion) is less proven than distilling
  verifiable tasks (math/extraction). A real research bet — validate empirically,
  don't assume.
- Heavy generation + the fine-tune itself want the grind box; dataset curation +
  formatting do not.
- Teacher MUST be Apache/MIT (Qwen/Mistral/DeepSeek). Never Llama/Gemma≤v3/frontier
  (contract strings). Qwen base = already clean.

## Repetition: prompt-only fix FAILED (2026-05-29) — it's architectural

Adding a hard anti-repetition rule to BEAT_PROMPT did NOT work: repetition 0.435 →
0.455 (flat/slightly worse) on different-personality. Reading the output diagnosed
WHY — the looping is ACROSS beats, from two structural causes a prompt can't fix:
1. **The bible's anchors ARE the repetition.** Every beat-call sees the SAME ~8
   anchors (breath-low, half-smile, jaw-unclenched, cool-glass, hips) because
   they're what the scene *is* — so each beat re-touches them. The bible's
   strength (binding the scene) causes the looping. Beats are generated blind to a
   global plan, so they can't know an anchor is "already used."
2. **Each beat re-establishes context** ("the glass shifts *again*," "breath
   *remains*") because it's a separate generation that doesn't trust the reader to
   remember. The staged-beat design that fixed DRIFT is structurally prone to this.
   (Credit: the new prompt DID add fresh material — the gaze, the floor grooves, a
   chuckle — it's additive, just not corrective.)

**Two real fixes (decide):**
- **(A) Distribute anchors across beats** — a planning step assigns each anchor to
  specific beats; each beat is told which are ITS anchors and not to dwell on
  others. Moderate change.
- **(B) Single-pass body with full plan visible** instead of N blind beat-calls —
  the model sees the whole arc, naturally avoids re-use (knows it "used" the glass).
  Bigger change / partly reverts staging — but staging was for length+drift, and
  scene-bible binding now does the drift job, so single-pass-with-plan may be viable.

**Deeper point for the model work:** this is exactly what FINE-TUNING fixes that
prompting can't — a model trained on non-repetitive scripts learns not to loop in
its WEIGHTS. The repetition fix and "make our own model" converge: the prompt/arch
fix yields better DATA; the fine-tune yields a model that doesn't need the prompt.

## v6 single-pass body: RESULT (2026-05-29) — architecture fix WORKS

On different-personality, three-way: old per-beat loop **0.435** → prompt-patch
**0.455** → **v6 single-pass 0.225** (repetition nearly halved). Also ~4× faster
(one call vs seven). Read confirms the metric: the looping is GONE — the body now
MOVES through the scene as a journey (party noise → answering calmly → glass set
down → a woman leans in → a man speaks → fade) instead of circling the same anchors.
**The single-pass architecture is the right foundation — keep it.** It's also the
general engine (good for any plan+anchors, incl. a stranger's own data).

Traded one big structural problem for two smaller, well-understood tuning ones:
1. **Too short** — 1277 words vs ~2200 target (single-pass's classic weakness, the
   original reason staging existed). Fix: length floor + continue-if-short, or
   raise target. Tractable, no revert.
2. **Example-anchor leakage** — "warmth across the top of your sternum",
   "fluorescent lights" copied semi-literally from the prompt's example anchors.
   Fix in anchor handling (we've seen this before).
   (Plus minor residual loops: "unapologetic about taking up space" ×3 — much
   better, not zero.)

Good trade: architecture is right; remaining issues are length + anchor-literalism,
both tractable, and both further softened later by the fine-tune.

## Immediate next step
Fix the generator so its output is training-grade (no looping/repetition), then
generate + curate the first clean batch. That batch IS the seed of our own model.
