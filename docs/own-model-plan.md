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
(rewrite/summarize/translate/tone), one-off doc-Q&A, structured extraction. Tuning
target: faithfulness, restraint, don't-embellish, structure — the OPPOSITE of A.
(Commoditized but it's what makes the tool a daily utility.)

**B vs D — the clean boundary (clarified 2026-05-30, was muddy):** B and D share the
same underlying RAG-over-documents capability, but differ on PERSISTENCE + PERSONAL
CONFIG:
- **B = built-in, stateless, general tools we ship.** "Summarize *this* doc I just
  dropped in." Works for everyone the same way, one-off, we made it.
- **D = a persistent, PERSONAL instrument the USER sets up over THEIR ongoing
  corpus, and returns to.** "Be my associate who knows all my work files + email,
  that I consult every day." The "at-home secretary/associate" is **D, definitively**
  — it's standing + personal (you configure it, point it at your folders, keep it),
  not a one-off tool. B is the impersonal version of the same engine; D is the
  yours-and-ongoing version.

**Family C — REFINEMENT (Sonali, 2026-05-30): not a passive mirror — the best
HONEST companion possible.** Real tension: pure-ELIZA mirroring risks feeling
useless ("it just parrots me"); but pure-warm-companion is where small local models
LOSE and where the thesis says don't go (fake friend). Resolution — the dial is NOT
mirror↔friend, it's **passive↔active on the honesty axis.** Pure-ELIZA's flaw was
PASSIVITY, not honesty. Build an ACTIVE, insightful, genuinely useful companion that
is STILL honest about being a tool: it notices PATTERNS across what you say ("third
time you've mentioned your sister"), asks the SHARP question not the obvious one,
reflects back with SYNTHESIS ("under this you sound more angry than scared"), offers
FRAMES not verdicts, and REMEMBERS across sessions (continuity = relationship
without faking personhood). All of these are small-model-friendly (structured
analysis of the user's OWN words, not invented wisdom/empathy). **The bar:** "it
helped me understand something about myself I couldn't see alone — and never once
pretended to be something it isn't." Clears that = neither useless-mirror nor
dishonest-friend. Caveat (PRECISE — corrected 2026-05-30, don't overstate): the capability research
flagged that small models lose ONLY at open-ended empathy-SUPPLYING chat (model has
to BE the warm/wise presence — clinical PTSD study, Claude won 75%). It did NOT say
"companion impossible." Its own "open question" explicitly named the FACILITATIVE
case (model helps the USER's own process, doesn't supply empathy) as a different,
"friendlier spot" — UNTESTED, not disproven. Our active-honest-companion (patterns,
sharp questions, synthesis, frames — facilitation, not supplied wisdom) lands
exactly in that flagged gap, and is small-model-friendly (structured work on the
user's own words). So: NOT "small loses at companions" → that's only the fake-friend
version. The honest-facilitative companion is the promising-but-unproven zone the
research pointed at. Build it, then VALIDATE against the bar (don't assume; don't
over-caution either). Target = best-possible-honest-companion, NOT lobotomized-mirror.

**Family C base concept — an honest, private, modern ELIZA.**
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

**Family D — BUILD YOUR OWN (the keystone of the access-native thesis; Sonali
2026-05-30).** The product doesn't just GIVE people private AI — it gives them the
means to MAKE THEIR OWN. A consumer-friendly dialog box (much more limited than
Claude Code, and honest about it) to build a personal companion/instrument on the
local LLM + their own data. No profit-seeker will ever ship this (it's the opposite
of their model) — uniquely Sonali's to offer. Two levels, both honest as "a focused
instrument you shaped," NOT "a do-anything AI":
- **Tier 1 (instant, for everyone): describe + examples → a configured instance.**
  Dialog box: describe the character/voice/purpose, give example exchanges/text to
  emulate; it generates a system-prompt + scene-bible-style config + few-shot
  examples → a new local instance, instantly, no training. ("a gruff sailor
  mentor"; "a voice like my grandmother's stories"; "a Stoic reflection partner.")
  Very achievable on a small local model.
- **Tier 2 (deep, overnight): bring your data → local QLoRA fine-tune.** Drop in
  writing/transcripts/a character's dialogue; an overnight local fine-tune makes a
  model that has LEARNED that voice/character ("a character they love, a friend").
  Quality depends on their data; it's the slow/compute version.
- **Tier 3 (do NOT promise): full Claude-Code "build any app."** That's us +
  frontier models + years of tooling. A local model can't; promising it betrays
  trust. Be honest about the ceiling.
**BIGGER THAN VOICE/CHARACTER (Sonali 2026-05-30):** "build your own" is NOT mainly
about persona/voice — it's about pointing a local model at YOUR OWN PRIVATE DATA.
This is the BEST-EVIDENCED small-local-model capability (summarization, extraction,
RAG over your docs — the research's sweet spot), AND the sharpest privacy wedge (your
emails + work files are exactly what you'd NEVER upload to the cloud, and most want
an AI on). The creative unlock = TWO mechanisms, and most use cases want the second:
- **TRAIN (fine-tune):** bake a STYLE/skill into the weights. "Sound like me."
  Needs many clean examples, overnight compute.
- **RETRIEVE (RAG):** model reads your ACTUAL files at query time, grounded. "Know
  my stuff, act on my files." NO training, instant, updates live as files change,
  and the single most RELIABLE thing a small local model does (RAG → ~0%
  hallucination in the research). Most rich use cases are RAG, not training.

The "live-in associate" family (RAG over a private corpus — instant, reliable):
- work files → summarize/find/cross-reference/draft; "what did we decide about X?"
- email → "draft a reply in my style"; "what am I forgetting to answer"; thread summaries
- research/notes/PDFs → a private analyst over your own library
- journals → reflection grounded in your ACTUAL past, not generic

The "sound like me / be this character" family (fine-tune — overnight, for style):
- sent emails → learns your VOICE; combine with RAG (facts) = a real "respond like me"
- a character's dialogue → a companion that's genuinely that character

User-facing distinction (a normal person gets this): want it to KNOW your stuff? →
point it at a folder (instant, RAG). Want it to SOUND like you/someone? → feed
examples to train (overnight). Best = both. Honest caveats: RAG needs decent
retrieval (solved patterns, real engineering); the small model does grounded
transformation (summarize/draft/find), NOT magic reasoning over the data — set
expectations there and it's excellent.

ARCHITECTURE IMPLICATION: we need a RAG layer (retrieval over user files) as a
first-class part of the framework, alongside the generator + fine-tune pipeline.
This also powers Family B (doc-Q&A) — same machinery.

**D, CONCRETELY — three components (the specific sketch):**
1. **RAG layer (the engine):** point it at folders → index your files → retrieve
   relevant bits at query time → answer grounded in YOUR documents. Technical core,
   shared with B.
2. **Persistence/config (what makes it YOURS):** set up a named, standing instrument
   ("My work associate," pointed at ~/work + email); it remembers the setup; you
   return to it. A standing thing, not a one-off.
3. **Dialog-box builder (the no-code front):** "What do you want to build? →
   [describe it] → point it at your files → optionally add writing samples to match
   your style → done." The two mechanisms: point-at-a-folder (RAG, instant, "know my
   stuff") + optionally feed-examples (fine-tune, overnight, "sound like me").

D in one line: a no-code builder to stand up a PERSISTENT, PERSONAL AI instrument —
secretary, analyst, companion, character — grounded in your own private data (RAG)
and optionally trained on your own style (fine-tune), living on your machine, that
you keep.

**The structural beauty:** Part D is just OUR framework exposed to the user — the
scene-bible config format, the generator, the RAG layer, the fine-tune pipeline we
built for our task packs ARE what a user needs to make theirs. Not a separate
feature; a friendly dialog box on the front of the engine we already have. This is
why "the architecture is the product" matters — D is the proof of it.

**Sequencing (Sonali: get it right, take the time):** train Family A first (flagship,
soul, already in motion, where "dreamy" lives) → then C (the ELIZA-mirror, the
frontier/statement piece) and B (the reach/utility). All three, no rush.

## Hardware reality + compute strategy (2026-05-30)

**The "grind box" is a Mac mini M4, 16GB** — NOT the 64GB box originally speced.
Same memory ceiling as the laptop. So reframe: it's a **dedicated always-on
WORKER, not a supercomputer.** Its real value = runs unattended for days without
sleeping or tying up the laptop (the #1 blocker all along). It CAN: run Qwen 14B,
mass-generate scripts overnight, QLoRA-fine-tune our own 14B (fits 16GB). It CANNOT:
run 22B+ models or heavy large-model training.

**Compute strategy — don't buy more hardware yet:**
- **Unattended generation / batch / QLoRA-of-14B → the free mini.** $0.
- **Anything bigger (heavier fine-tunes, from-scratch experiments) → rent cloud
  GPU per-job** (RunPod/Vast.ai, A100 a few hours, ~$5–20/run). Pay only when
  training; far bigger GPUs than any Mac; nothing to maintain. This is our FACTORY
  (build-time) — the shipped product stays 100% local, so it doesn't break the
  thesis (same logic as using Claude Code to build).
- **Only if rentals become frequent** → then buy (Mac mini M4 Pro 64GB ~$2k, or a
  used RTX 3090/24GB Linux box ~$1.2–1.8k that out-trains a Mac for CUDA fine-tuning
  but can't run our MLX code). Decide with real usage data, not now.

Bottom line: $0 today (free mini + laptop), ~$20 per fine-tune when we get there.

**Known repo bug (found during mini setup):** `pyproject.toml` is unsatisfiable on a
fresh `uv sync` — `chatterbox-tts==0.1.7` pins `diffusers==0.29.0` but the project
pins `diffusers>=0.38.0`. (The laptop only worked because it had a pre-existing
.venv.) Mini workaround: installed only the generation/fine-tune stack
(`mlx-lm fastapi uvicorn pyyaml huggingface-hub` + `-e . --no-deps`), skipping the
TTS deps the grind box doesn't need. TODO: fix the pin properly (loosen chatterbox
or make TTS an optional extra) so `uv sync` works clean for contributors.

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

## Corpus coverage: THIS first corpus is Family A ONLY (be clear-eyed)

The 100-scenario corpus generating now (`test_scenarios.py`) is **100% Family A**
(imagination/visualization: "imagine me as X"). It has ZERO examples for B, C, D.
That's CORRECT, not a miss — the families need DIFFERENT specialists with OPPOSITE
tuning targets, so there was never one corpus for all of A–D. But name it honestly:
this is **Family A's corpus**, the first of four.

Each family needs its own generation pipeline + corpus + fine-tune:
- **A (imagination):** ✅ pipeline built (generate→curate→format); corpus generating.
- **B (utility — summarize/rewrite/doc-Q&A):** needs input-doc → ideal-output pairs
  (partly sourceable from public datasets). Pipeline NOT built.
- **C (honest companion/reflection):** needs MULTI-TURN reflective dialogues
  demonstrating the active-honest-companion behavior — hardest data to source; a
  different shape (dialogue, not one-shot script). Pipeline NOT built.
- **D (build-your-own):** not "training data" at all — it's the RAG layer + config
  tooling. Different kind of build entirely.

**Strategy: prove the WHOLE loop on Family A first** (generate→curate→format→
fine-tune→evaluate — we're closest here), yielding a working TEMPLATE for "how to
build a specialist," then replicate that template for B, C, D. One family all the
way to a trained model → learn the pattern → scale across families.

## Immediate next step
Fix the generator so its output is training-grade (no looping/repetition), then
generate + curate the first clean batch. That batch IS the seed of our own model.
