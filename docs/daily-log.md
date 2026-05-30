# Daily log

A rolling record of the daily grind. Newest entry on top. Each entry: what
moved, what the numbers said, and the decision queue for the next session.
The journey is part of the public diligent narrative — see `strategy.md`.

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
