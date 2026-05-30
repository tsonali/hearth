# Product roadmap — a curated suite of private structured experiences

## Product identity (the decision)

We are **not** shipping an open chatbot. We ship a **curated suite of structured,
private, audio-capable experiences.** For each one we (a) tell the user *what it's
for*, (b) set *what to expect*, and (c) *architect the pipeline* so the result is
genuinely good. Opinionated, designed instruments — not a do-anything text box.

This is doubly grounded: the capability evidence says small local models win at
*structured/specialized* tasks and lose at open chat; and the thesis says give
people *instruments, not companions*. Curation is both the smart bet and the
honest one.

## Cross-cutting architecture — how we make every use case effective

Every experience is a **task pack** built on shared framework machinery:

- **A protocol** — the structured pipeline (classify → bind a curated structure →
  staged generation → assemble). The Imagination Engine's `classify → scene-bible →
  staged beats` is the template.
- **A curated structure-library** — scene bibles / prompt templates / frameworks,
  hand-designed (Sonali's taste), so the model *fills in* a good design instead of
  improvising. This is the quality lever.
- **A task-specific eval rubric** — we tune each pack against its own rubric until
  it clears a bar (the immersion rubric, generalized).
- **Reliability scaffolding** — robust structured output + staged generation
  (built).
- **An optional audio layer** — render to speech (user's own voice, or a system
  voice) for the experiences where audio matters.
- **A model** — see model strategy below (one base + per-task LoRA specialists).
- **Honest framing** — each pack ships with plain "here's what this does and what to
  expect," set deliberately (no overpromising; "instrument, not companion").

## Model strategy — "multiple models" is cheaper than it sounds

The naive worry: bundling several full models is huge (each small 4-bit base is
~2–8 GB). The real architecture avoids that:

- **One shared base model** (a small 4-bit model, ~5–8 GB) loaded one-at-a-time
  (16 GB RAM runs any single small model fine — multi-model is a *disk*, not a
  *RAM*, concern; you load the one a task needs and swap).
- **Per-task specialization via LoRA adapters** — a fine-tuned adapter is **tens to
  low-hundreds of MB**, layered on the shared base. So "a different model per task"
  is really *one base + many tiny specialists* — per-task quality at minimal extra
  disk. (This is the Phase-2 distillation plan, made packageable.)
- **Download-on-demand** — ship a lean base + voice; fetch a task's adapter (and, if
  ever needed, an alternate base) the first time the user opens that experience.
  Install stays small; disk grows only with what they actually use.
- Near-term (before fine-tunes exist): pick the best off-the-shelf base per task —
  and *test which base wins which task* (a real, cheap experiment). Long-term:
  fine-tuned LoRA specialists per task.

**Verdict: not prohibitive.** One base + per-task LoRA adapters + on-demand download
gives per-task models for roughly the footprint of a single model plus a handful of
small files.

## Use-case catalog (initial)

Each: what it is · what we tell the user to expect · audio? · the structured architecture.

1. **Imagination Engine** (flagship, proven) — personalized guided-imagination
   session. *Expect:* a ~12-min eyes-closed session in your own voice. *Audio: yes.*
   *Arch:* scene bibles + staged beats.
2. **Wind-down / sleep / meditation** — calming guided audio to reset or fall
   asleep. *Expect:* a short spoken session, no thread to return to. *Audio: yes.*
   *Arch:* near-identical to imagination (shared pipeline, different protocol +
   structure-library).
3. **Structured journaling & reflection** — reads your entry, mirrors it, asks 2–3
   targeted questions, tracks patterns over time. *Expect:* a private space that
   helps *you* think — not advice. *Audio: optional* (read prompts aloud). *Arch:*
   reflect-and-prompt (bounded), retrieval of your own past entries.
4. **Rehearsal** (hard conversations / interviews / pitches) — practice against a
   defined counterpart with constraints; brief feedback. *Expect:* realistic
   practice, privately. *Audio: optional* (it speaks the other role). *Arch:*
   structured roleplay (fixed scenario + persona), brevity/turn constraints.
5. **Decision-thinking** — walks a private decision through a method (pre-mortem,
   values, pros/cons). *Expect:* it runs you through a framework, doesn't hand you
   an answer. *Audio: no.* *Arch:* fixed framework + structured prompts.
6. **Make sense of my own stuff** — summarize/organize your private notes, journal,
   day. *Expect:* clarity over your own mess, on-device. *Audio: optional.* *Arch:*
   summarization/extraction (the strongest proven small-model skill).
7. **Personal writing help** — rewrite/proofread sensitive personal writing.
   *Expect:* polish, nothing leaves your machine. *Audio: no.* *Arch:* rewriting
   (proven on-device strength).
8. **Memory / life-story capture** — structured interview prompts to record your
   life. *Expect:* a private keepsake. *Audio: yes* (read back). *Arch:* interview
   protocol + retrieval.

## Sequencing

- **Now:** nail the Imagination Engine (scene bibles + binding + eval) as the proof
  the task-pack architecture produces quality.
- **Next (cheap, shared pipeline):** wind-down/meditation — nearly the same pipeline,
  validates "task pack = swap protocol + structure-library + voice."
- **Then:** structured journaling/reflection and rehearsal (test the constrained-
  interaction techniques: brevity, ask-don't-tell, reflect-back).
- **Cross-cutting, ongoing:** the audio layer (bake in across audio use-cases), the
  per-task model/adapter strategy, and per-task eval rubrics.
- **Phase 2 (grind box):** fine-tuned LoRA specialists per task pack.
