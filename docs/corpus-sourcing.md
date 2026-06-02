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
