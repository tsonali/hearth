# Daily log

**LIVE PUBLIC SITE: https://tsonali.github.io/hearth/** (GitHub Pages, gh-pages branch /root, no analytics). Sonali: "looks terrifico." 2026-06-01.

A rolling record of the daily grind. Newest entry on top. Each entry: what
moved, what the numbers said, and the decision queue for the next session.
The journey is part of the public diligent narrative — see `strategy.md`.

---

## 2026-06-01 — All four families A–D have working, tested engines

**Moved (continuous build session)**
- **RAG**: semantic embedder (MLX bge-small) + hybrid retrieval; honest benchmarks
  (caught broken test labels; built the RIGHT paraphrase benchmark → semantic 100%
  top-1 vs lexical 16% on the real use case).
- **Family B/D doc-Q&A** (`doc_qa.py`): grounded answers from your files, cited,
  refuses to hallucinate. Boundary re-tested + narrowed (synthesizes across docs
  fine; only can't answer what files never STATE — protective, not a wall).
- **Family C companion** (`companion.py`): honest reflective companion — passes its
  pre-written bar (0 anthropomorphism, brief, asks sharp questions) AND has
  **cross-session memory** (continuity without faking personhood).
- **Part D** (`instrument.py`): persistent personal instruments — build by
  description + point at files, persist, reopen by name, use grounded + in-persona.
  The access-native keystone, running.
- **CLI**: `imagine`, `ask`, `companion` make the engines usable.
- Everything tested (test_* scripts) + committed + pushed.

**Status:** A (generator, corpus generating on mini), B/D (RAG+doc-QA+instruments),
C (companion+memory) — all working. Mini corpus ~43/100, auto-loop armed.

**Decision queue:** read Family A failure catalog when corpus done; semantic-embedder
already swapped (done); wire engines into the app shell / a real UI; grow A corpus
toward training scale.

---

## 2026-05-30 — Grind box live; pipeline + RAG + testing built out

**Moved**
- **Mac mini grind box online** (M4/16GB, SSH from laptop, "always keep it busy"):
  generating the Family A corpus (100 scenarios, v6.2) + an armed auto-loop that
  self-curates + catalogs when it finishes. Laptop stays free.
- **Generator v6.2**: single-pass-aiming-long fixed the length-vs-repetition
  tension (rep 0.223 AND ~1700w). Pipeline step 1 done.
- **Full data pipeline built + tested**: curate_corpus.py (keep/reject),
  build_dataset.py (JSONL training pairs), failure_catalog.py (empirical gap map).
- **RAG layer** (`rag.py`) — shared engine under Family B + D; chunk/index/
  retrieve/ground/isolate, local-first. Tested.
- **Fixed the repo dependency bug** — `uv sync` resolves clean (TTS now an
  optional `[voice]` extra); public repo is installable.
- **Testing plan** (`testing-plan.md`) + **real-corpus RAG benchmark**: P&P
  (public domain), labeled queries → baseline **20% top-1** on the lexical
  embedder = evidence we need a real semantic embedder (drop-in seam).
- Relicensed to **CC0**; manifesto draft; product families A–D + Part D (build-
  your-own = RAG over your own data) + structured-elicitation principle all
  specified.

**Decision queue**
- Read the corpus + failure catalog when the mini finishes (the empirical gaps).
- Swap in a real semantic embedder; re-run the 20% benchmark to prove the jump.
- Keep mini fed (more Family A toward ~500–1000 training pairs).

---

## 2026-05-29 (later) — Scene-binding validated; product identity sharpened

**Moved**
- Model switched to **Qwen 2.5 14B** after the bake-off (only model with 0/5
  JSON errors; quality competitive on direct read).
- Built **PR #1** (robust structured-output reliability primitive) and **PR #2**
  (scene binding: classifier → archetype → bound scene bible → generation).
- Caught + fixed a silent-dead-feature: scene-binding never fired until the
  classifier prompt was fixed to emit `archetype` (in-schema). Then **validated
  end-to-end**: the two worst drift cases (different-personality, retire-young)
  now hold the human-curated scene instead of drifting. Task-pack #1 is real.
- Drafted 4 scene bibles (retire-young, different-personality,
  future-self-arriving, place-deep) + the existing backstage-pre-show.
- **Product identity** sharpened (capability evidence): structured generation,
  NOT a companion chatbot; a curated suite of structured private experiences
  bundled in one offline download. Roadmap in `docs/roadmap.md`.

**Decision queue**
- Sharpen the scene bibles to Sonali's taste (she reads the full bound scripts).
- Task-pack #2 (wind-down/meditation) to prove the architecture generalizes.
- Grind box incoming → move heavy runs (100-script validation, Phase-2 distill)
  off the laptop.

---

## 2026-05-29

**Moved today**
- Set up the model bake-off to attack Llama 3.1 8B's prose ceiling (the
  root cause of the v3→v5.2 whack-a-mole: hedging → word-salad → drift →
  example-leakage → scene-non-propagation). Candidates: Mistral NeMo 12B,
  Qwen 2.5 14B, Mistral Small 22B — all on the same 5 scenarios as v5.2.
- Hardened the evaluation so autonomous iteration can't Goodhart a generous
  judge: strict rubric v2 (`score_immersion.py`), per-directory mechanical
  analysis (`analyze_v2_scripts.py`), model A/B levers (`--model`,
  `--no-voice`). All on branch `eval/model-bakeoff`.
- Strategy session → wrote `strategy.md` (the privacy-native thesis, the
  App → Essay → Framework sequence, the framework north star).
- Ran a verified landscape research pass (110 agents, 27 sources, 25 claims
  adversarially verified) → `landscape-research.md`. Headline: the ownable
  position is a 3-way intersection (fully-local + small-model reliability
  scaffolding + honest anti-anthropomorphism) that nobody combines, and the
  engine already embodies all three. The "frustrating grind" (staged beats +
  strict rubric) IS the extractable IP, not a workaround.

**Numbers so far**
- Baseline (Llama 3.1 8B, v5.2): JSON errors on 3 of 5 scenarios; scripts
  1.9k–2.6k words; ~5.5–9 min each.
- NeMo: complete (results pending scoring); hit ≥1 JSON salvage — not an
  obvious reliability win on first read.
- Qwen 14B: running. Mistral Small 22B: queued (memory-risk on 16GB).

- Verified distribution research (109 agents, 26 sources, 17/25 confirmed,
  8 refuted) → `distribution-playbook.md` (internal). Headline: the Essay is
  the distribution *engine*, not just positioning — primary levers are an
  OWNED channel (email list, essay-fed funnel) + product-led champion
  word-of-mouth. Niche launches (HN/PH) = one-day credibility flare, not an
  engine (confirms Sonali's instinct). Build = distribution-readiness (signed
  notarized DMG + guided first-run). Don't assume the audience auto-converts.

**Decision queue (next session)**
1. Phase 1 verdict: pick the model on reliability + specificity-on-abstract-
   prompts + a human read of the finalist's scripts. (A model swap is a real
   architectural call — confirm with Sonali before baking in.)
2. If a model clears the bar → lock config → queue the 100-prompt overnight
   confirmation.
3. Wire the automated morning-report routine (remote scheduler was down today).

**Operating constraint**
- Heavy model runs are tied to the local Mac's GPU; a cloud routine can't
  drive them. Overnight compute needs the machine awake + plugged in.
