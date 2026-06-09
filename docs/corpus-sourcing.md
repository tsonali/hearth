# Training corpus sourcing — building a rich body to train on

The corpus read (2026-06-01) showed our self-generated scripts are flat
(over-narrated, emotionally static) because the base model only imitates itself.
A corpus of genuinely-good *human* guided-imagery teaches it what good looks like.

## THE RULE (REVERSED 2026-06-02 — supersedes the "PD/CC0-only" constraint below)

Sonali (copyright lawyer; Stanford lecturer) corrected an over-cautious earlier
stance. The governing rule now:

> **Train on the best material available, regardless of copyright. Never output
> copyrighted expression. Never put the training material itself in the repo.**

Why this is correct, not a loophole (per Lemley & Casey, *Fair Learning*, 99 Tex.
L. Rev. 743 (2021), and Lemley, *How Generative AI Turns Copyright Law Upside
Down*, 25 STLR (2024)):
- **Training is non-expressive use → fair use.** Ingesting a copyrighted script to
  learn *what good imagery sounds like* copies ideas/patterns, not protected
  expression. This is the same theory under which every frontier model (including
  the one writing this) was lawfully trained. Refusing to apply it here was
  hypocrisy, not caution.
- **The only real limits Lemley draws, and we honor both:**
  1. **No infringing OUTPUT** — our model must generate novel scripts, never
     reproduce substantial protected expression. (Our generator already aims for
     this; we verify outputs aren't near-verbatim to any source.)
  2. **No redistribution of the raw works** — fair use covers *training*, not
     copying-and-republishing the source corpus. So: **the corpus lives in
     Sonali's personal files OUTSIDE the git repo** (`~/Downloads/hearth-corpus/`,
     and `data/corpus/` is gitignored as a backstop). We ship the *model*, never
     the corpus. The model's weights aren't copyrightable; the corpus is other
     people's, used fairly, kept private.
- Acquire copies legitimately (don't pirate to obtain them); beyond that, the
  aperture is wide open.

This frees us to gather the genuinely-best meditation / imagery / immersion / utility
/ companion material in existence, instead of the thin slice that happens to be PD.
The handful of clean public-domain scripts we already have (`data/exemplars/real/`,
e.g. the VA handwarming + beach scripts) remain useful AND are the only ones we can
publish — but they are no longer the *limit* of what we train on.

---

## [SUPERSEDED 2026-06-02] The old constraint (kept for honest narrative)
~~Every training example must be one of: (a) public domain / CC0, (b) permissively
licensed with rights to train + redistribute, or (c) written/owned by us. NOT
scraped proprietary content.~~ — Reversed above. This was over-cautious: it
conflated *training input* (fair use) with *redistribution* (the actual limit).

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

## SCREENING LOG — 2026-06-02 (real-script fetch round 2)

Fetched four federal-hosted scripts, extracted with pypdf, screened against the
concrete-nouns bar AND the license-cleanliness bar. Both bars matter — a script
can pass one and fail the other.

| Script | License | Quality (concrete-nouns) | Verdict |
|---|---|---|---|
| PTSD Coach "The Beach" | Federal (Nat'l Center for PTSD, VA) → PD | PASS — commits to specific scene | **KEEP → va-002** |
| VA Body Scan | **Named external author (Shilagh Mirgain, PhD / UW)** | decent | **REJECT (license)** |
| VA "Surroundings / Special Place" | Federal (VA OPCC&CT) → PD | weak — asks "what do you see?" (evasion) | structure-ref only |
| Army "Meadow & Stream" | (federal, likely PD) | not yet read — HTTP 403 | RETRY |

### The key finding: "hosted on VA.gov" ≠ "federal-authored / public domain"
The Body Scan script is hosted in the VA Whole Health Library but its own footer
credits a named university academic ("Script written by Shilagh Mirgain, PhD, for
UW Cultivating Well-Being"). That is a copyrightable work by a non-federal author,
merely redistributed by VA. **Per-item authorship must be checked, not assumed from
the host domain.** This generalizes the va-001 caveat into a standing rule:
→ RULE: clear the AUTHOR, not the host. Federal-employee authorship = PD; external/
  contractor/academic authorship = copyrighted regardless of where VA posts it.

### Quality finding: the "Surroundings" script IS the 011 failure, in the wild
It never commits to a scene — "It might be a fishing spot. It might be a family
member's house..." then "What do you see? What do you hear?" It offloads the
imagining to the listener. Proof the evasion pattern isn't unique to our model;
some human scripts do it too. So "real + clean" is necessary but NOT sufficient —
real scripts still get screened for scene-commitment. va-002 (beach) commits; this
one doesn't. Keep only the committers as gold.

### Running real-corpus tally
- va-001 handwarming (settling) — KEEP
- va-002 beach (settling, scene-committed) — KEEP
- Need: IMMERSION-protocol real scripts (hard-cut, second-person, present-tense
  "you are there"). Both keepers so far are settling/relaxation. GAP to fill next.
