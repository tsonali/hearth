# Training corpus sourcing — where good, CLEAN guided-imagery examples come from

The corpus read (2026-06-01) showed our self-generated scripts are flat
(over-narrated, emotionally static) because the base model only imitates itself.
A corpus of genuinely-good *human* guided-imagery would teach it what good looks
like — better than bootstrapping off its own mediocre output. But the data must be
as CLEAN as the code: our whole thesis is owned, unencumbered, public-domain-able
data. So no scraping Headspace/Calm/YouTube meditation transcripts (copyright AND
hypocritical). The corpus has to be sourced honestly.

## The constraint (non-negotiable)
Every training example must be one of: (a) public domain / CC0, (b) permissively
licensed with rights to train + redistribute, or (c) written/owned by us. NOT
scraped proprietary content. This is the same discipline as the Apache-only
distillation teachers — clean inputs → a clean, dedicatable model.

## Candidate sources (ranked by quality × cleanliness)

1. **WE WRITE A SEED SET (cleanest, highest-quality, hardest).** Sonali (the protocol
   designer) + Claude hand-write a small number — 30-100 — of *exemplary* scripts
   that nail restraint + emotional arc + her taste. Small but pristine; the LIMA
   result says ~1000 clean examples beat 5000 noisy, and a few dozen *perfect* ones
   anchor the style. This is the gold core. Doubles as the eval gold-standard.

2. **Public-domain adjacent literature (free, large, indirect).** Guided imagery is
   close to: second-person literary passages, hypnosis scripts in old public-domain
   texts, Gutenberg works rich in sensory description, classic relaxation/auto-
   suggestion texts (e.g. early-20th-c. works now public domain — Coué-style
   autosuggestion, old hypnotism manuals). Not turnkey "sessions" but real prose
   modeling sensory/second-person voice. Mineable, fully clean.

3. **Permissively-licensed meditation/script collections, IF they exist.** Some
   public-domain or CC0 meditation script collections and therapy-worksheet banks
   exist. Must verify license per source (CC0/CC-BY ok; CC-NC ok for our
   non-commercial use; all-rights-reserved out). Research needed.

4. **Synthetic-from-a-strong-teacher, curated (the bootstrapping path, cleaned up).**
   Use an Apache/MIT open teacher (or, one-time/offline, a frontier model — but only
   if the OUTPUT is then heavily human-curated, and noting the ToS caveat for
   *distributed* models) to draft, then RUTHLESSLY curate to only the genuinely-good.
   This is what we've been doing; the read showed raw output isn't good enough, so
   the curation bar must be a *human/Claude read*, not just the mechanical floor.

5. **Public-domain audio → transcripts.** LibriVox-style public-domain spoken-word,
   or public-domain relaxation recordings, transcribed. Clean but quality varies.

## COURSE-CORRECTION (2026-06-01): stop AI-drafting exemplars; get REAL ones

Sonali's call after reading the hand-drafted exemplars: they're "way too AI-y."
The honest diagnosis — you can't bootstrap genuine quality from the model that
lacks it; Claude drafting "plausible meditation prose" reproduces exactly the
problem. We need REAL human-authored examples as the gold standard. So:
- PAUSE Claude-written exemplars (001-011 were the AI-y batch; keep as scaffolding/
  structure reference only, NOT as gold).
- Decision: **lean toward PUBLIC-DOMAIN + GOVERNMENT/institutional scripts** (free,
  clean, real, on-thesis — our training data being public-domain is itself the
  point) — pending the deep-research report (run wf_5b7fee2c-259) on concrete
  sources, licenses, prices. Commissioning real practitioners is a live option too;
  decide once research lands.
- Hard constraint reaffirmed: training data must be public-domain / openly-licensed /
  owned-with-train+redistribute rights. NO scraping Headspace/Calm/etc.

## THE FAILURE, NAMED PRECISELY (Sonali, 2026-06-01): abstraction, not imagery

Sonali on the AI-drafted 002: "pure nonsense — nothing happened — the opposite of
vivid imagery." Correct and damning. The real failure mode (worse than "AI-y"):
**when Claude lacks the concrete specifics, it retreats to ABSTRACTION and emotional
NARRATION instead of committing to real, physical, specific things in a real scene.**
- BAD (what Claude wrote): "a space where the weight used to be," "the steadiness of
  having earned it," "you are someone who finishes." → feelings *described*, no scene,
  nothing happening. A pep talk, not an imagining.
- GOOD (what vivid imagery is): the cold doorknob, the smell of toast, the specific
  crack in the ceiling, the weight of a particular mug, the floor against the soles
  of the feet. Mundane, physical, SPECIFIC. Something concrete in each moment.
This directly violates the immersion research (attentional capture + sensory
specificity) that we had IN HAND — proof Claude can't self-source this quality.
THE BAR for the real corpus + any future generation: commit to the concrete physical
specific; never flee to the grand abstract. "Feel the floor under your feet," not
"feel the steadiness of having arrived." Real practitioner scripts have exactly this
courage-of-the-mundane-specific — which is precisely why we need THEM, not Claude's
abstractions.

## THE DEEPEST FAILURE: placeholders, not things (read 011 to see it)

Read 011-effortless-skill closely (Sonali made me): it is ALL pronouns and
placeholders — "the thing," "it," "the moment," "the hard part," "the next part,"
"the skill," "the ease." NOT ONE concrete noun. It's a Mad Libs template where every
real thing is a [BLANK] never filled in. A meditation about a *blank*.
- The self-deception: Claude told itself "let it be wherever that is for you" was
  RESTRAINT (leaving room for the user). It is not — it is EVASION of the work of
  imagining a specific scene, dressed up as generosity. Vagueness isn't generous;
  it's empty.
- The fix understood: real imagery COMMITS to a specific scene even if the user's
  differs. "Your fingers on the piano keys, the third slightly sticky" / "the bow
  drawing across the string, the note landing true" transports; "the moment to use
  it arrives" is nothing. Specificity is generous; placeholders are a form letter.
- Why it happened: Claude had no real scene to anchor to, so it filled with
  pronouns. Exactly why we need REAL human scripts — a teacher would write "you sit
  at the desk and the report writes itself, sentences arriving fully formed," never
  "the skill runs ahead of you."
THE TEST for any script (real or generated): can you point to the concrete nouns? If
it's mostly "it/the thing/the moment," it's a placeholder template, not imagery.

## Recommended approach (combine)
- **Anchor: hand-write ~30-50 exemplary scripts (source #1)** — Sonali's taste, the
  restraint+arc the read found missing. These are the quality north star AND eval set.
- **Scale: self-generate against the FIXED generator (v6.4+), curate with a Claude
  READ (not just metrics)** — the read is the bar now. Keep only what matches the
  hand-written exemplars' quality.
- **Enrich: mine public-domain sensory/second-person prose (source #2)** for style
  transfer / continued-pretraining signal on the *voice*, separate from task pairs.
- Everything logged with provenance + license, so the final dataset is publishable CC0.

## Open questions
- How many hand-written exemplars can Sonali realistically produce / approve? (Sets
  the quality ceiling.)
- Do clean public-domain guided-imagery collections exist at scale? (Needs a research
  pass — but framed by the clean-only constraint.)
- For task pairs we need (intake → script); public-domain prose gives style, not
  pairs. So pairs come from #1 (hand) + #4 (generate+curate); prose (#2) is for voice.
