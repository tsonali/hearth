# Testing plan — how we know any of this actually works

We've been testing ad hoc. This is the robust plan: WHAT to test, HOW, and with
WHICH real data — layer by layer, because each layer fails differently. Principle:
**test on REAL data and against REAL expectations, not toy fixtures** — toy tests
prove plumbing; real corpora prove behavior. (Proven already: indexing P&P showed
the RAG plumbing scales but the lexical embedder retrieves poorly on real prose —
a gap a 3-doc toy test hid.)

## Three kinds of test, per layer

1. **Mechanical / unit (fast, deterministic, no model):** does the plumbing work?
   Run on every change. (e.g. `test_structured.py`, `test_scene_binding.py`,
   `test_rag.py` plumbing.)
2. **Behavioral / quality (needs model + real data):** is the OUTPUT good? Measured,
   not vibes — metrics + a human/Claude read. (e.g. corpus repetition/engagement
   scores, retrieval hit-rate on a labeled query set.)
3. **Regression:** did a change make something that worked WORSE? Keep baselines;
   compare every iteration (the v5→v6→v6.1→v6.2 repetition trail is this done right).

## Per-layer test design

### Structured output (`structured.py`) — DONE, good
Unit tests cover the 5 real malformations + clean + unrecoverable. Keep as-is.

### Generator / scene-binding (Family A) — partial
- Mechanical: `analyze_v2_scripts.py` + `failure_catalog.py` (repetition, hedging,
  stock, length, prompt-engagement, leakage) over a corpus. ✅
- Behavioral: needs a **rubric score + Claude read** on a sample, and ideally
  eventual **human (Sonali) taste rating** + (later) listening to audio.
- **Gap:** no fixed labeled "these scenarios SHOULD produce X" set yet; we judge
  by failure-mode absence, not target-match. Acceptable for now.

### RAG (Family B + D) — plumbing done, quality UNVALIDATED
- Mechanical: `test_rag.py` (chunk/index/retrieve/isolate). ✅
- Behavioral: **retrieval hit-rate on a labeled query set over a REAL corpus.**
  Test data secured: `data/test_corpus/pride_and_prejudice.txt` (Project Gutenberg,
  public domain — on-thesis). Build a labeled set: ~15 queries ("the first
  proposal scene") → the passage/chapter that SHOULD be the top hit; measure
  top-1 / top-3 accuracy.
- **Measured gap (2026-05-30):** lexical HashingEmbedder retrieves poorly on real
  prose (missed the proposal scene). → **real semantic on-device embedder is now
  evidence-backed, not speculative.** Re-run the same labeled set after the swap to
  prove the upgrade.

### Companion (Family C) — not built; hardest to test
- Behavioral testing is intrinsically hard (open-ended dialogue). Plan: a set of
  **scripted user turns + the bar** ("helped me understand something; never faked
  personhood") rated by Claude/human across multi-turn transcripts. Define when built.

### Fine-tuned model (Phase 2) — define before the first fine-tune
- The decisive test: **specialist vs. base-Qwen+scaffolding, same inputs, blind
  read + mechanical floor.** Held-out scenarios NOT in the training set (no leakage).

## Real corpora to test on (public-domain / clean — matches the CC0 ethos)
- **RAG:** Project Gutenberg books (P&P secured); for "associate over work files,"
  a synthetic-but-realistic doc set (meeting notes / emails we write) since real
  private data can't be shared.
- **Family B (summarize/rewrite):** public datasets exist (e.g. CNN/DailyMail-style
  summaries, public email corpora like Enron for "respond like me" style tests) —
  evaluate when B's pipeline is built; prefer permissively-licensed sets.

## The discipline
- A `scripts/test_*.py` for every module; run them before committing engine changes.
- Keep baselines (a metrics row per generator version) so regressions are caught.
- Real data + labeled expectations for behavioral claims — never "looks good to me."
- Honest about what a test does NOT cover (plumbing ≠ quality).
