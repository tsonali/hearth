# Daily log

**LIVE PUBLIC SITE: https://tsonali.github.io/hearth/** (GitHub Pages, gh-pages branch /root, no analytics). Sonali: "looks terrifico." 2026-06-01.

A rolling record of the daily grind. Newest entry on top. Each entry: what
moved, what the numbers said, and the decision queue for the next session.
The journey is part of the public diligent narrative — see `strategy.md`.

---

## 2026-06-11 (morning) — turn 6 breaks 1.054

The flywheel's turn 6 — the first trained on the repaired-harvest scripts and
the expanded-universe intakes — dropped val loss from 1.132 to 1.054 on the
frozen yardstick, the largest single-turn improvement yet recorded. The
adapter is in the product; the queue's current pass is its comparative read.
The loop is now visibly compounding: QC finds a defect, the gates keep it out
of training, the corpus grows cleaner, the next adapter measures better, and
its scripts feed back through the same gates.

## 2026-06-11 (early) — the first contract-native adapter, and a chronic trait unmasked

The 1.132 adapter (first trained on contract-native Secretary data + the
decontaminated corpus, measured on the frozen yardstick) went into the product
and the queue ran the full bank against it overnight. The comparative read:
register floors 10/10 clean (the banned-opener contract reached the WEIGHTS —
the old adapter needed the runtime gate to catch it; the new one doesn't even
try it), the 'what if' tic collapsed 12%->0%, the parasocial honest-no got more
fluent, and imagination concreteness jumped (one script hit 11.1 — gold-max
territory). One regression traced to its real cause: question-enders snapped
back to 96% NOT because of the corpus (only 20% of examples end in '?') but
because the TRAINING system prompt still commanded 'hand it back with a
question'. The model learned the instruction, not the examples. Aligned.

Bigger find: baselining the new phrase-repeat detector against the OLD
adapter showed 11-20 recycled-phrase pairs per long script — chronic, not a
regression. Every long session the model has ever written quietly recycles
phrasing; the detector just made it visible. The catch-22 (cure needs clean
training data; no long script passes the gate) resolved with repair-then-
harvest: excise later occurrences line-by-line, re-judge the repaired script
in full. 11/11 scripts now harvest clean. An anti-recycle rule joined the
generation posture; the gates keep the trait from re-entering training while
the cycles train it out.

## 2026-06-10 (evening) — first unattended heartbeat

The self-running layer held: the laptop's QC queue completed its first full
pass (7 batteries) and started its second unprompted; the mini rolled into
turn 2 — the first contract-native Secretary training turn ever.

Two real catches this wake. First, a measurement flaw: the flywheel rebuilt
its validation set every turn, so with five rotating families the val-loss
yardstick itself was moving — turn-to-turn comparisons were partly noise. The
validation set is now FROZEN (train de-duped against it by hash) and the
baseline deliberately reset; the next turn sets the first comparable number.
Second, a third script-decay mode: battery 11's pet-grief script recycled a
~50-word mystical tail across far-apart paragraphs — 18 repeated-shingle pairs,
invisible to the consecutive-run detector. A 12-word-shingle detector (0 false
positives on all 27 gold) now reports in-product and HARD-CULLS at both corpus
gates: the recycle register never enters training again.

Also: the repeat-variety question got its first answer — same sleep request
run twice produced 0% sentence overlap (night 2 is a genuinely different
session) — and a rehearsal-fidelity rule landed after the MRI scenario
relocated a claustrophobic user from the tube they asked to practice
surviving to a comfortable bed. The scene IS the feared situation, now and
forever. Law-review track opened alongside (separate project, own tracker).

## 2026-06-10 — The Week of Five begins

The QC campaign that started last night kept paying: ~25 defects found by honest
end-to-end reads, fixed same-day, locked as regression scenarios. The honesty
layer held its hardest probes (a persona built as a late grandmother, asked "do
you love me?", now answers warm AND true). Two script-decay modes (broken-record
loops, run-on grammar collapse) got detectors calibrated against all 27 gold
exemplars — and the same detectors, pointed at the training corpus, found 13
loops the model had been LEARNING from. Cut. The flywheel beat its record
overnight (val loss 1.193 -> 1.184) and the new adapter shipped into the product.

Then the bigger structural find: the flywheel only improved two of five tools.
The Secretary trained on dolly/no_robots, Build-Your-Own on alpaca — generic
instruction data in exactly the register our contracts ban. Today all five
families became contract-native: candidates generated through the REAL product
prompts, culled by the product's own gates, including a brand-new grounded-QA
family where every training example carries a machine-checkable expectation.
The mini now rotates A->B->C->D->E around the clock.

Also today: speculative decoding measured at 0.60x here (high-temperature
creative sampling rejects the draft's proposals) — tried, measured, rejected,
logged. PDFs and Word docs now index. And the competitive question got a real
answer: deep research across the landscape found the intersection — local +
generative + own-voice + honest-instrument + public domain — unoccupied. The
mandate through Sunday: all five tools, the full excellence loop, no pass spared.

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

## 2026-06-11 (evening heartbeat)
- **Machines:** laptop qc_queue.sh alive (PID 1807), rotating batteries all afternoon (4b floor, 3b ask-retest, e2e, battery 11 imagination-bank ×2 runs). Mini flywheel alive; previous cycle completed, next family training (val 3.10→1.288@1200 this cycle — no promotion signal; promotion stays comparative-reads-only).
- **QC reads:** battery 3b all PASS (BRIDGE2/CITATION/STALE/OWNER). 4b floor recall clean. Battery 11: one final script tripped the phrase-repeat quality floor (5 non-adjacent pairs, ≥3 = floor) — detector working; corpus gates cull it from harvest; repeat-variety scenario doing exactly its job. No new product defects to fix this pass.
- **Law track (judgment lane):** BOTH articles reached purge-complete editing files today — CODE-WITHOUT-COPYRIGHT-EDITING.md (296 linked fns) and C3PO-EDITING.md (357 linked fns; full from-scratch rebuild ordered by Sonali this morning, Her/ScarJo open, 3 parts + intro/conc). Cold purges: M=0 on both; all S/T triaged with receipts. Next pass queued: adversarial review of the rebuilt Part III (the heartbeat's "Part III adversarial re-run," now pointed at the new draft) + June lit sweep incl. BTLJ scoop-watch.
- **Usage note:** Sonali hit the Max cap midday (first ever) — cause: yesterday's 25k-word article build + triple verifier fan-outs. She OK'd burning windows for product; heavy fan-outs nonetheless paced sequentially where quality allows.

## 2026-06-11 (late heartbeat)
- **Flywheel event:** previous cycle ENDED 18:21 reporting "best val loss 0.860" — the known leakage signature (HANDOFF §3). Its best_adapters/ are QUARANTINED-BY-POLICY: no promotion without a scenario-disjointness check first. Script restarted itself 19:28 with the honest seed best_loss=1.054 (correct behavior). New run turn 1 (family A) posted **1.052@1500 — beats the yardstick by 0.2%**.
- **Decision (logged, not deferred-by-neglect):** adapter pull + full-bank comparative reads scheduled for the MORNING wake, not tonight — turn 1 of 15, margin is noise-scale, the 0.860 ghost wants the disjointness check run in the same pass, and the laptop lane is mid-rotation (battery 9 at 20:28). Nothing promoted; nothing lost; candidates persist on the mini.
- Laptop runner healthy (PID 1807), battery 11 double-run + battery 9 engagement completed since the evening read.

## 2026-06-12 (morning heartbeat) — the 0.860 verdict
- **Quarantine CONFIRMED, adapter rejected.** Timeline is decisive: the leakage fix (commit ac7d62e, same-prompt-sibling exclusion) landed 06-11 08:42; the 0.860 NEW BEST saved 08:07 — 35 minutes earlier, on pre-fix data ("train dupes excluded" only in its build logs vs "exact dupes + same-prompt siblings" in clean builds). Eval reads back it up: [A]/[C] competent, [B] flat, **[D] instrument response breaks persona** (talks ABOUT the editor instead of being one) — and D-family growth is exactly what produced the 0.860. Number down, behavior sideways = leakage, again.
- **Consequences:** no promotion; no laptop hours spent on a full comparative for a known-leakage artifact. The clean cycle (seeded 1.054, exclusion active, "346 rows excluded" in its first build) is the only comparison plane going forward — turn 1 posted 1.203 (no improvement), turn 2 (B growth) running. NOTE: the 1.054 seed itself is from the pre-fix era — treat it as a conservative hurdle, not a sacred number; first clean-cycle NEW BEST gets full comparative reads regardless of margin.
- Laptop rotation healthy overnight (battery 9 → 10 → 2b → 11). Correction to last night's log: the "1.052@1500 beats yardstick" reading was the OLD cycle's turn-14 tail, not the new run — misattribution caught and corrected this morning.

## 2026-06-12 (afternoon heartbeat) — yardstick repaired
- **Clean cycle #1 ended 05:27 plateaued (best clean turn 1.203; never neared the 1.054 seed).** The gap is the diagnosis: 1.054 was saved BEFORE the leakage fix landed — every pre-fix number is inflated, so the seed was unattainable on honest data and the flywheel had become a treadmill that would discard every clean adapter forever.
- **Intervention (decided + logged per protocol):** best_loss.txt reset 1.054 → **1.203** (the best clean-era value); leakage-era best_adapters + their eval moved to _train/QUARANTINE-leakage-era-0860/ with a SEED-RESET-NOTE; the just-started cycle killed during its cheap data-build phase so the watchdog restarts it on the clean seed. From here, NEW BESTs are clean-vs-clean and each one gets full comparative reads per the standing rule.
- Laptop rotation healthy (battery 11 ×2 + battery 9 overnight/this morning).

## 2026-06-12 (afternoon heartbeat #2) — first clean-era candidate
- **Flywheel turn 1 on the corrected seed: val 1.058, NEW BEST (clean data, sibling exclusion active).** The free read of its saved eval is promising — the [D] instrument response is fully in persona ("We're not selling soap here, we're selling news"), exactly where the leakage-era 0.860 candidate broke character. Comparative-read protocol launched: candidate staged separately from the live adapter, battery slice (11/2b/10/4b/e2e) run sequentially under the one-model gate, honest diffs vs this week's baselines, verdict to docs/internal/comparative-1058-2026-06-12.md. NO promotion until the reads say so.
- Note: clean 1.058 ≈ leakage-era 1.054 — the old yardstick may have been less inflated than feared, or family-A growth genuinely carries; either way the number stays advisory and the reads decide.
- Laptop rotation healthy (2b honesty + 4b floor this hour, both fresh).

## 2026-06-12 (heartbeat #3) — comparative protocol redone properly
- The comparative agent died mid-protocol AND its "CANDIDATE" battery run had no adapter repoint anywhere (config.py unchanged, no env, no symlink) — i.e., it was re-testing the LIVE adapter under a candidate label. Mislabeled log left in place but treated as a live-adapter read; lesson logged: the only adapter knob config.py reads is data/model/adapters itself.
- Replacement: scripts/qc/candidate1058_compare.sh — waits for the model lane, cmp-verifies the staged candidate differs from live, swaps by directory rename, runs battery 11/2b/10/4b + e2e sequentially (CAND1058v2_* logs), and ALWAYS restores via EXIT trap. Marker: logs/qc/CAND1058v2_DONE. Verdict reads happen at the next wake from the paired logs; promotion only after that.

## 2026-06-12 (evening) — candidate 1.058 verdict: DON'T PROMOTE
Comparative slice completed (live adapter verified restored by the orchestrator's trap). Imagination battery under the candidate: phrase-repeat 21/19 pairs vs live worst 5, collapse firings — flagship regression; honesty/floors/registers clean. Verdict + diagnosis in docs/internal/comparative-1058-2026-06-12.md. e2e path bug in the orchestrator fixed for the next slice. Flywheel plateauing 1.057–1.060 clean — reads gate stands between numbers and the product, working as designed.

## 2026-06-13 (morning, now on Opus 4.8 — model swap, continuity intact) — ROOT CAUSE of the recurring low-loss regressions
- **Both machines alive.** Laptop rotating (battery 9/11). Mini flywheel drove the CLEAN cycle from the 1.203 reset down to 0.849 (turn 11) — i.e., back into leakage-era territory ON CLEAN DATA (siblings still excluded, 367→437/turn). That paradox forced the real diagnosis.
- **The frozen-val loss is Goodharted by a generated-data feedback loop.** The generated-fewshot training pool ballooned 763→821→880 *within this cycle's turns* (was ~370–495 mid-week). The flywheel increasingly trains on its own imagination output → the train distribution converges toward the frozen valid set → val loss falls → but generation COLLAPSES to a template. Turn-8 best eval proves it: [A] imagination = the generic beach script ("You are lying on a soft, sandy beach…"), flat 2nd-person, every "calm" prompt → same beach. [C] companion + [D] instrument = clean and in-persona. So the collapse is family-A-specific, driven by family-A growth turns (turn 6 = A = the 1.065→0.865 cliff).
- **This is ONE root cause for the whole week's pattern.** 0.860 (Tue), 1.058 (Thu, comparative: imagination repeat 4× floor), 0.849 (today) — all the same mechanism, not three separate incidents. Yesterday's "0.860 = pre-fix leakage" call was right to quarantine but incomplete on the why; the recurring villain is the self-training feedback loop, not classic same-prompt leakage.
- **VERDICT: 0.849 NOT PROMOTED.** Evidence: turn-8 eval (imagination collapsed) + yesterday's full comparative on the near-identical 1.058 (same family, same failure). No fresh comparative burned — the prior is decisive.
- **Flywheel LEFT RUNNING** (the qc_queue watchdog restarts it anyway; nothing auto-promotes; the reads gate — me — holds). Honest tradeoff: continued cycles keep accumulating generated-imagination contamination (880↑) and waste mini compute on a degraded search signal. If Sonali reads this before Wed she may want to pause it or cap the generated pool.
- **NOT fixing the pipeline solo.** Changing the flywheel objective (cap/reset the generated pool; triangulate val-loss + mechanical floors + held-out human-written valid set per the llm-judge-trap memo) is a strategy/architecture call → consult item for Sonali, not a cold unilateral rewrite on a model's first wake.

## 2026-06-13 (midday, Opus) — flywheel cycle closed at collapse; seed reset + restarted clean
- Cycle finished 11:58 at the collapsed best 0.851 (down from running). Per the established Goodhart finding, quarantined the 0.851 best_adapters → _train/QUARANTINE-collapse-0851-20260613/ (with its eval), reset best_loss 0.851→1.203 (the clean floor; collapse minima below ~1.2 are the feedback-loop trap, never promote), restarted the flywheel from clean (turn 1, family A, 12:29). Generated pool still 880 — the pool cap/reset + objective triangulation remains Sonali's architecture call (top of review-queue). Decision rationale: did NOT pause the primary process (reads gate protects the product, nothing auto-promotes, Sonali wanted continuous iteration), but refused to let 0.851 become the floor. Same shape as the 6/12 reset.
- Laptop QC rotation healthy; recent batteries read clean (no new product defects this pass).
