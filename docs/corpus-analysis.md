# Corpus read & analysis — 2026-06-02 (first big gather)

I gathered ~582 MB across the four use-case families, then **read representative
samples myself** and judged them against the quality bars we've set (vivid-concrete
imagery for A; honest non-advice mirror for C; useful text-transforms for B; broad
instruction + persona following for D). The tally is in the manifest; this is the
*judgment*.

## The headline finding

**The two families defined by a CONTRARIAN VOICE cannot be bulk-sourced. The two
defined by CAPABILITY can.**

- **A (imagination)** is defined by a *voice* — vivid, concrete, restrained, scene-
  committed. The internet's "meditation" data is the opposite: generic, warm-AI,
  abstract, or expository.
- **C (companion)** is defined by a *stance* — an honest mirror that reflects and
  questions, never advises, never fakes feelings. The internet's "therapy" data is
  the opposite: advice-dispensing with mild fake-empathy.
- **B (utility)** and **D (build-your-own)** are defined by *capability* —
  transform-this-text, follow-this-instruction, adopt-this-role. Bulk data fits.

So for A and C, **training on the bulk would regress us toward the exact mean we
define ourselves against.** Their moat is curation against our own exemplars (our
taste), not volume — the LIMA "few perfect beat many noisy" result, and the whole
Hearth thesis (be the un-generic alternative) applied to data.

## Family-by-family (what I read)

### B — Utility ✅ TRAIN-READY
Sample (no_robots): *"Please summarize the goals for scientists in this text: …"* —
a clean task + real content to transform. Exactly right. Dolly, DialogSum, Enron
subject lines, no_robots all give genuine instruction→artifact pairs. **Keep all;
this family is healthy.** (Already shipped the engine that uses this: the Secretary,
`/utility`.)

### D — Build Your Own ✅ MOSTLY TRAIN-READY
Alpaca / OpenOrca / SlimOrca / Open-Platypus give broad instruction-following;
roleplay + persona sets give role-adoption (D's distinctive need). Breadth is the
point here, and we have it. **Two fixes:** (1) `Synthetic-Persona-Chat` is weak —
bland chit-chat with literal "[user 1's name]" placeholders; drop or down-weight,
the richer roleplay sets cover persona better. (2) SlimOrca logged ~0 words (nested
`conversations` schema, not a real problem — data is present; my word-counter just
didn't traverse it).

### A — Imagination ❌ BULK FAILS THE BAR
What I read, ranked:
- **AlbertoB12 (844):** *"Welcome to our mindfulness meditation session today. I'm so
  glad you're taking this time for yourself to cultivate greater focus and clarity…"*
  → the **exact AI-y, abstract, affirmation voice Sonali rejected.** EXCLUDE from gold.
- **mindfulness-alpaca (7,697):** expository *advice about* meditation ("strategies
  individuals with ADHD can use… 1. Start small…"). Not scripts. Training on it
  teaches the model to *lecture about* meditation — the over-narration failure.
  EXCLUDE from script training.
- **guided_meditations_hf (21):** medical *articles* ("MRI… decreasing cytokine…
  telomere shortening"). Wrong type entirely. EXCLUDE.
- **jhana (99):** real transcribed metta meditation — *"imagine in your heart a very
  large beautiful flower garden… pick that person a bouquet… see the joy in their
  eyes."* Scene-committed, progresses, has timing markers. **KEEP — mid quality**
  (committed but not maximally sensory-specific; "amazing varieties of colorful
  flowers" rather than named, textured detail).
- **The real gold remains the hand-found PD scripts** (`data/exemplars/real/`: VA
  handwarming + beach) and the **Lusk book** — concrete, named, physical.

→ **Conclusion:** of ~8,600 bulk A examples, ~8,500 are AI-y / expository / articles.
Only ~99 (jhana) + the handful of VA/Lusk are real script-quality. **Volume did not
help, exactly as predicted.** Clean guided-imagery *scripts* essentially don't exist
as HF datasets. Path forward for A: a small **real gold set** (VA + jhana-good + Lusk
+ deliberately-sourced practitioner scripts/books) used BOTH as the curation bar and
as seed; then generate-against-exemplars with a hard Claude read. Quality core, not
bulk.

### C — Companion ⚠️ BULK IS THE WRONG MODE
- **fadodr (3.88M words — the BIGGEST C set):** *"One possible approach to addressing
  your social anxiety is through gradual exposure…"* and *"I can understand how
  difficult it must be for you… It takes a lot of courage…"* → **advice-dispensing
  AND mild fake-empathy.** Both are explicitly forbidden by the Companion spec
  (no verdicts, no "I feel/understand"). The single largest C file is the wrong mode.
- **Amod (3,512):** blunt directive advice — *"If everyone thinks you're worthless,
  then maybe you need to find new people to hang out with."* Verdicts, not mirroring.
  Wrong mode.
- **counsel-chat (2,775):** real therapists; professional and not fake-friendly, but
  reassurance/advice-leaning — *"Therapists are completely ready and equipped…"*.
  Usable with filtering toward its reflective turns.
- **AnnoMI (motivational interviewing):** the **only true style match** — reflective
  listening + open questions, the honest-mirror stance. ⚠️ The mini's pull of AnnoMI
  came back tiny/wrong-field (432 words); **use the laptop's good copy (~153K words).**

→ **Conclusion:** anchor C on AnnoMI; filter counsel-chat toward reflective turns;
treat the advice-dispensing bulk (Amod, fadodr) as **negative/contrast** examples
(what NOT to do), not positive training. Likely also generate MI-style reflective
data against the AnnoMI exemplars.

## What this means for the plan
1. **B and D:** proceed to a fine-tune with the bulk as-is (minus the two D fixes).
2. **A and C:** do NOT dump bulk in. Build small curated gold sets against our
   exemplars; generate-and-curate for volume. This is where Sonali's taste is the
   product — and it's defensible IP precisely because it can't be scraped.
3. Data hygiene to fix: drop mindfulness-alpaca/guided_meditations_hf/AlbertoB12 from
   A-as-scripts; re-pull AnnoMI properly on the mini (or sync laptop's); fix the
   word-counter's nested-schema traversal (cosmetic).
