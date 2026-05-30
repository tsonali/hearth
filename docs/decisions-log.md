# Decisions Log

A running record of decisions and their reasoning. Append a new entry whenever a decision is made or changed. This keeps the *why* from getting lost as the project evolves.

---

## Initial decisions (project setup)

**Product is a local-first guided-imagination tool, not a generative-video product.**
The imagery happens in the user's mind; the product generates words and voice. This is truer to the underlying mechanism (mental rehearsal / guided imagery) and avoids dependence on expensive, cloud-bound frontier video models. Reason: fidelity to the therapeutic mechanism + local-first economics align.

**Modality is audio-led, internally-imaged.** Text core (reasoning) drives a local TTS voice layer. Reason: voice is the modality where high-quality, on-device, zero-marginal-cost generation is genuinely achievable now; and guided imagery is traditionally and effectively audio-led.

**Local-first, no cloud inference, no token meter, fully private.** All model and TTS inference runs on the user's device; no user content leaves the machine. Reason: this is the core trust proposition for a product holding the user's inner life, and the central differentiator versus anything the large model companies would ship.

**v0 is ONE template: future-self visualization.** Other protocols are deferred. Reason: build concrete first; the flexible multi-template "platform" is extracted later from real templates, not designed up front.

**Future-self visualization chosen as the first template (over grief/trauma/exposure).** Reason: it is non-clinical — a mediocre v0 session is merely unhelpful, not harmful. Trauma- and grief-adjacent protocols can re-traumatize if delivered by a rough first version, and the intimate audio modality raises those stakes. Those protocols remain on the roadmap but require de-escalation machinery and clinician input designed in — not a v0 concern.

**The conversation layer is scoped to intake and reflection, not companionship.** Reason: the product is an instrument the user opens to do focused work and then closes — not a standing emotional companion. Companion-style drift would undermine the product's coherence and the user's wellbeing.

**Target the founder's own machine (Apple Silicon Mac) first.** Cross-platform is deferred. Reason: prove the full loop end-to-end on one machine before generalizing.

**Build approach: founder directs Claude Code; no cofounder or ML hire for v0.** Reason: the v0 as scoped is a tractable assembly of mature building blocks (local model runners, local TTS, local database). The genuinely hard work — reliable cross-machine operation, packaging for non-technical users, the long edge-case tail, ongoing ownership of a live product — arrives at the platform/scaling stage and will be assessed concretely when the project reaches it.

---

## 2026-05-26 — Task 01 stack and posture

**Open-source primitives only; no third-party orchestrators (Ollama, LM Studio, etc.).** Inference is built directly on `mlx-lm` (Apple's open-source MLX library, MIT). Model weights are pulled directly from Hugging Face. Reason: a meaningful part of this project's purpose is to *own* the inference stack — not abstract it behind someone else's wrapper. This sharpens the `local-first` and `private by construction` principles: ownership of the engine itself, not just ownership of the data. If we ever need cross-platform reach beyond Apple Silicon, the engine seam (`src/imagination_engine/inference.py`) is the swap point — most likely to `llama.cpp` via `llama-cpp-python`.

**Inference engine: MLX-LM (Apple).** Choice between MLX-LM and llama.cpp for the v0 inference primitive. MLX-LM wins for v0 because: (a) v0 targets the founder's M3 Mac specifically, where MLX is the fastest native option; (b) MLX is an entirely separate engine lineage from Ollama (which wraps llama.cpp), so the "own the stack" story is strongest with MLX; (c) the inference seam in `inference.py` is small, so a future swap to llama.cpp for cross-platform v2 is cheap.

**Model: Llama 3.1 8B Instruct, 4-bit MLX quantization** (`mlx-community/Meta-Llama-3.1-8B-Instruct-4bit`). On 16 GB unified memory this leaves comfortable headroom for the OS, the FastAPI process, and a future TTS engine. Llama 3.1 8B is well-tuned for natural English dialogue, which matters for warm intake conversation and protocol-driven generation. Open weights under the Llama 3.1 Community License.

**App shell: Python + FastAPI + Uvicorn + a single static HTML page on `127.0.0.1` loopback.** No Tauri or Electron for v0 — we already need Python for the inference, DB (Task 05), and TTS (Task 04) layers; adding a Node/Rust toolchain just to draw a window is a deferred concern. The server binds to loopback only. We can wrap in a Tauri shell later for a real `.app` icon.

**Project layout: real Python package under `src/imagination_engine/`, managed with `uv`.** Modules: `inference.py` (the engine seam), `server.py` (FastAPI), `config.py` (single source of truth for paths/model), `__main__.py` (CLI entry: `serve` / `probe`), and `web/` (the static HTML + CSS). Reason: see next decision.

**Build-quality posture for v0: invest in the foundation, not throwaway-and-rewrite.** Explicit founder direction overriding `CLAUDE.md`'s "ugly is fine, ugly-but-whole beats elegant-but-partial" default *for this project specifically*. The principle now is: the Task 01 commit should be code we'd happily extend through Tasks 02–05, not code we throw away. This does **not** override `build concrete, extract abstractions later` — we still won't build the protocol-engine abstraction before two protocols exist. It only raises the quality bar on the foundation itself.

**Python 3.13 via `uv`-managed venv.** The system Python is 3.14.2 — too new for current MLX-LM wheels (March 2026: mlx-lm 0.31.x targets 3.10–3.13). `uv` installs 3.13 side-by-side without touching system Python.

---

## 2026-05-26 — Scope reframe: imagination engine, not future-self engine. No guardrails.

**The protocol is one universal scaffold: settle → user's chosen imagining → return → reflection.** What used to be called "future-self visualization" was actually the universal shape of guided imagination, applied to one specific framing. The product is now correctly framed as an **imagination engine** that lets the user choose *what* to imagine — themselves succeeding, themselves as a different character, their life differently, being Abraham Lincoln, being Taylor Swift, anything else they describe. The structure stays constant; the content is the user's.

**This does NOT violate "build concrete, abstract later."** We're still building one protocol scaffold concretely. We're just acknowledging that the scaffold is more general than the original "future-self" framing implied — and that the intake should be open-ended rather than forcing a single mode. No new protocol docs needed; one architecture, infinite content.

**Audience: adults, small beta.** Not strangers downloading it off the internet (yet). Reflective people Sonali would actually hand it to.

**No content guardrails.** Adults have sovereignty over their own imagination. The engine doesn't filter, refuse, or topic-block — it helps the user imagine whatever they want. Decision and reasoning logged in [[project-no-guardrails]] (memory). One legal floor (sexual content involving minors) stands not because we impose it but because it's already law and the base model refuses it. Llama 3.1's trained-in RLHF refusals are the only friction; we'll write the generation system prompts to grant permissive posture, and if those refusals become a real blocker we'll swap to an uncensored base model (separate decision).

**Intake conversation (Task 02) starts here.** Will be designed next.

---

## 2026-05-27 — Distribution + positioning

Decisions taken during a planning conversation while the overnight voice fine-tune was running.

**Distribution: website only, no App Store.** Direct download from a website, signed with an Apple Developer ID and notarized (so Gatekeeper trusts it). Reasoning: (a) Apple's review would almost certainly object to voice-cloning of arbitrary voices + the no-guardrails content posture + the multi-gigabyte locally-running LLM outside Apple's Foundation Models framework; (b) even if approved, every update goes through review again with the same rejection risk, which is not a stable position for a product whose identity is *no guardrails*; (c) website-only means Apple doesn't even see the install graph — purer privacy. Notarization is the only Apple touchpoint, and that only sees the binary, not the user.

**Marketing position: lead with privacy.** Earlier draft argued for "privacy as quiet infrastructure" (Apple's playbook). Wrong for an unknown brand pushing a privacy-radical AI download. Trust has to be *built*, not assumed. Privacy is the headline because it's the only reason a stranger would dare install this.

**Privacy is verifiable, not just claimed.** The trust comes from evidence the user can check themselves:
- The code is open source. *"Don't trust us — read the code."*
- "Turn off your WiFi" is a verifiable claim, not a promise.
- No account, no email, no sign-up. Nothing to leak because nothing exists.
- A live "🟢 offline · 0 bytes transmitted" indicator in the app itself.
- Engineering-honest "How it works" page describing the actual data flow.

**Sonali Maitra is the named author of the product.** Her authorial work (*God in the Machine* on AI and unwarranted authority, *Unreality* on AI-blurred experience) is the product's positioning anchor. The product is the book's thesis made operational. Author provenance is a primary trust signal alongside the open-source code. Explicitly decided NOT to be anonymous.

**Voice = the user's own voice.** No modulation toward future-self / past-self / etc. The user records their own voice; the engine renders sessions in that same voice. Different *imaginings* (future-self, character, counterfactual) are content choices in intake; the voice itself is just the user. Simpler, and closer to the deeper thesis: *we always look to others for guidance, but in the end it's only ever yourself — so why not have you talk to yourself.*

**Repo: public from day 1, voice data scrubbed from history.** GitHub repo will be public; the code is the trust signal. Sonali's voice recordings and trained checkpoints stay off the public repo (they'd enable impersonation if shared). History rewrite removes the existing commit that added them before the first push to GitHub.

### Task 01 outcome — empirical numbers from the founder's M3 (16 GB)

- Model: Llama 3.1 8B Instruct, 4-bit MLX. Fetched once from Hugging Face (~80 seconds, ~4.5 GB on disk).
- Cold load: **2.5 s** from local cache.
- Generation: **17.7 tokens/sec** (steady state).
- Prompt processing: 132 tokens/sec.
- Peak memory: **4.69 GB** — ~11 GB headroom for OS + FastAPI + future TTS layer.
- Offline proof: server restarted with `HF_HUB_OFFLINE=1` and `TRANSFORMERS_OFFLINE=1` (both libraries' network code paths forcibly disabled). Inference worked unchanged. The architectural bet — *local-first, no network dependency once the model is on disk* — holds.

These numbers are good enough that Task 03 (~1500-token full-session generation) will take ~85 seconds wall-clock, and Task 02 (intake conversation with streaming responses) feels responsive at human reading speed. No model swap needed for v0.

A pleasant unsolicited signal: with only the protocol's voice convention given as a system prompt, Llama 3.1 8B produces output that is genuinely in the future-self register — second person, present tense, sensory, paced. The protocol-as-prompt approach in build-plan/03 looks viable without fine-tuning.

---

## 2026-05-26 — Voice pivot: Kokoro is not the v0 voice

**Decision: stock TTS voices (Kokoro, Piper, etc.) are disqualified as the v0 production voice.** Kept Kokoro in the codebase as a development / fallback voice (fast renders, useful for quick checks), but the user-facing session voice will not be a stock speaker.

**Why:** Sonali listened to `af_heart` (Kokoro's warmest default) and immediately identified it as "way too AI-y... the generic AI woman." For a product whose mechanism depends on the user closing their eyes and surrendering to a voice's guidance, the unmistakable affect of stock TTS collapses the experience back into "I'm being talked at by a chatbot." This validates the warning in `build-plan/04-voice-layer.md`: voice quality is a make-or-break gate. Found out early — exactly as the build plan intended.

**New direction: full fine-tune of an open base TTS model on Sonali's own voice, ~30+ minutes of clean recorded audio.** Not voice cloning from a short reference (Level 1) — *fine-tuning* (Level 2): we produce a model whose weights are adapted to Sonali's voice, lives in this repo as our own artifact. The architectural choice and product principle is captured in [[project-voice-design]] (memory).

**Base model: F5-TTS** (SWivid, MIT, late 2024). State-of-the-art small-model voice quality, active community fine-tuning recipes, supports both zero-shot cloning *and* fine-tuning so the same install is single-purpose-free.

**Recording setup:** USB microphone (model TBD), a quiet room. Reading material: phonetically balanced sentences + guided-imagery register samples, ~200 sentences total, broken into 15–20 min recording sessions to avoid voice drift.

**Why this matches the project's posture:** [[feedback-oss-only]] says no third-party orchestrators. [[feedback-build-properly]] says invest in a real foundation. [[project-voice-design]] says the voice is the product. All three converge on this choice — the v0's voice should be an artifact we made, voicing the founder, owned end-to-end.

The Kokoro code (`src/imagination_engine/tts.py`, `/speak` endpoint, "Read aloud" button) stays in the codebase. It's useful for dev iteration and as a fallback. The fine-tuned F5-TTS model will become the production path when training completes.

---

## 2026-05-28 — Generator overhaul v3: immersion not meditation

**Problem:** v2 (post real-living-people fix) was still producing soft, hedging, generic scripts that abandoned the user's actual creative prompt. Quantitative analysis on 87 v2 scripts:

- **Body-engage rate 0.39** — only 39% of user prompt keywords made it into the body. **15+ scripts at 0.00** — the model abandoned the prompt entirely (e.g. the body of `029-retire-young` doesn't say retire, young, or wealthy anywhere; `032-husband-adore` doesn't say husband or adore).
- **9.3 hedge phrases per script on average** ("you might notice", "perhaps", "maybe", "if you'd like"). The meditation-app sound baked in by COMMON_POSTURE's voice rules.
- **Body median 472 words vs 1800-word target.** The model was stopping early at ~25% of the requested length.
- **Stock peaceful imagery recurring across unrelated scenarios** — candlelight, meadows, brooks, wildflowers showing up in romantic scripts, achievement scripts, becoming-different-personality scripts. The AI's safe default for "peaceful."
- **Qualitative read of 4 representative scripts**: Harry Styles got Generic Romantic Hero with "Harry" find-and-replaced; different-personality got Hallmark meadow + word-salad tail; mistake-never-happened got generic childhood summer with no engagement of the actual prompt.

**Research check on the opening stage.** Founder asked: is the slow body-settle opening grounded in immersion research, or is it inherited meditation convention? Sub-agent surveyed four literatures: Ericksonian hypnotic induction, PETTLEP sport-psychology visualization, Green & Brock narrative transportation, lucid/hypnagogic imagery induction. Convergent finding across all four: **immersion comes from attentional capture + sensory specificity, NOT somatic relaxation.** PETTLEP literature is explicit that pre-imagery relaxation REDUCES functional equivalence with the imagined state. The slow body-settle is meditation-tradition, not immersion-tradition.

**Decision: full prompt overhaul (v3) along three axes.**

1. **OPEN (renamed from settle):** 90-120 seconds, NOT 3-5 minutes. Now receives the intake transcript so it can hard-cut directly into the user's scene. Three moves: (a) Ericksonian utilization — name what's already true for the listener ("you're hearing my voice, your eyes are closed"); (b) single-point sensory anchor — narrow attention to one thing; (c) HARD CUT into the scene with the first concrete sensory anchor of the imagining. Skip "release the day" entirely — it primes a therapy frame and burns the freshest attention on suppression. Target ~150-200 words.

2. **IMAGINING (body):** hard rules in the prompt itself, not just suggestions. Explicit forbidden-phrase list ("you might notice", "perhaps", "maybe", "if you'd like", etc. — 15+ banned phrases). Explicit forbidden stock imagery list (candlelight, meadows, brooks, wildflowers — unless user named them). Mandatory prompt-engagement rule ("every 3-4 paragraphs make concrete reference to the user's specific imagining"). Sensory specificity rules (every paragraph names at least one concrete physical detail with body-part/object specificity). Length floor stated explicitly: "AT LEAST 15 PARAGRAPHS. AT LEAST 1800 WORDS. If you find yourself wrapping up at 500 or 800 words, YOU ARE NOT DONE."

3. **BACK (renamed from return):** carry-back MUST be ONE specific concrete detail pulled from the body of the script — not generic feelings. Five-move structure: soften image / carry-back / re-room / eyes open / one final line. No "wiggle fingers and toes" boilerplate. Target ~150-200 words.

**COMMON_POSTURE rewritten** to invert the hedging-as-virtue rule. Old: "Invitational language: 'you might notice,' 'perhaps,' 'if you'd like.' Never commanding." New: "FORBIDDEN PHRASES: 'you might notice'/'perhaps'/'maybe'/'allow yourself to'/... — these produce the meditation-app sound, which is the OPPOSITE of immersion. REPLACE THEM with the thing itself. Not 'perhaps her hand finds yours' but 'her hand finds yours.'"

**Empirical validation:** small probe batch of 5 scenarios spanning failure modes (003-taylor-swift, 031-harry-styles, 005-different-personality, 011-photographic-memory, 029-retire-young) running into `logs/scenario-tests-v3/`. Side-by-side comparison with v2 will drive the next iteration. No more 100-scenario batches until v3 is nailed.

**Citations for the research check** (in case future versions need to re-examine the opening): Holmes & Collins (2001) PETTLEP model; van Laer et al. Extended Transportation-Imagery Model meta-analysis; Green & Brock (2000) narrative transportation; Ericksonian induction; HIT/MILD lucid-imagery protocols. Full sources in the sub-agent transcript.

---

## 2026-05-29 — Model bake-off; switch to Qwen 2.5 14B; the model isn't the bottleneck

**Context.** The v3–v5 generator iterations were whack-a-mole against Llama 3.1 8B's ceiling: fix hedging → get word-salad → fix that → get prompt-drift → get JSON-parse failures (3 of 5 scenarios). Diagnosis: the 8B model is the bottleneck. Decision (with founder): run a head-to-head bake-off across local models that fit 16GB, and in parallel begin scene-bible scaffolding.

**Method.** Same 5 scenarios through the identical v5.2 generator on four models: Llama 3.1 8B (baseline), Mistral NeMo 12B, Qwen 2.5 14B, Mistral Small 22B. Evaluated on three legs to avoid Goodharting a single metric (see [[feedback-llm-judge-trap]]): (1) mechanical floor — JSON-parse failures, etc.; (2) a *strict* LLM-judge rubric v2 (rebuilt because the prior judge saturated at 5.00); (3) **direct reading of finalists by Claude**.

**Results.**
- **Mistral Small 22B: disqualified.** ~12–13GB exceeds the 16GB target with no headroom for the voice layer + app; it crashed the founder's laptop. Can never ship on the product's own target hardware. (Will run only on a dedicated grind box.)
- Strict-judge overall: NeMo 4.48 > Llama 4.28 > Qwen 4.24 — but spread is within noise at n=5.
- **JSON reliability — the thing the exercise was meant to fix:** Qwen **0/5** errors; Llama and NeMo **3/5** each. Only Qwen solved it.
- Speed/script: Llama ~6.5 min, NeMo ~10.6, Qwen ~17.4.

**The judge-trap, caught in the act.** Direct read overturned the judge: Qwen's Harry-Styles script was scored embodiment 1/5 by the local judge, but reading it, it is a *correct, vivid* CASE-B embodiment (listener present, Harry's hand finds theirs). The weak 8B judge mis-scored it, understating Qwen. Lesson logged: **for small batches Claude reads directly; the local 8B judge is retired from the eval loop; at 100+ scale use a panel of Claude agents, not a weak local model.** Conflating "the *product* is local-first" with "our *dev eval* must be local" was a category error.

**Core finding.** Direct reads of NeMo and Qwen on the abstract "different-personality" prompt show *both* drift (NeMo → eroticized café; Qwen → stage/mic scene + leaked the prompt's example anchors). **The model is not the bottleneck — the missing layer is reliability scaffolding** (scene bibles that *bind* the scene + robust structured output). This independently matches the landscape research's conclusion.

**Decisions.**
1. **Base model → Qwen 2.5 14B 4-bit.** It uniquely solved JSON reliability (the stated problem), quality is competitive once the judge's error is discounted, and its only cost is generation speed — acceptable for batch/overnight, especially on the incoming grind box. (Founder corrected an initial speed-first framing: priority is quality → reliability → speed.)
2. **Next work = scaffolding, not more model-shopping:** scene bibles to bind the scene and kill drift; harden JSON parsing / structured output. This is the extractable IP (see strategy.md).
3. **Eval:** Claude is the evaluator at current scale; mechanical floor always; Claude-agent panel for the 100-prompt confirmation. Retire the local Llama judge.

---

## 2026-05-29 — Model roadmap: scaffolding now, then distill our OWN specialist

**Framing correction (founder):** the framework's defining pillars are technical/access — *private & local + anti-token (own-don't-rent) + anti-massive-model (small models on your own hardware)* — i.e., **democratize private AI so the everyday person is unshackled from Big Tech AI.** Anti-anthropomorphism is the founder's personal/product stance, NOT part of the framework definition. (strategy.md updated to match.)

**The model work is two phases:**
- **Phase 1 (now): reliability scaffolding** on an off-the-shelf small model (Qwen 2.5 14B) — scene bibles that bind the scene (kill drift) + robust structured output (kill JSON breakage). This also *generates the dataset* for Phase 2.
- **Phase 2 (after): distill our OWN specialist model.** Not pre-train from scratch (frontier-lab compute, out of reach) — *distill/fine-tune*: (1) generate a large, ruthlessly-curated corpus of excellent guided-imagination sessions via the scaffolding + a strong teacher; (2) LoRA/QLoRA fine-tune a small open base on-device (MLX, grind box); (3) eval the specialist vs. off-the-shelf+scaffolding on the rubric + Claude reads + mechanical floor; (4) iterate. Endgame: a small, *owned*, on-device LLM specialist in immersive guided imagination — the language-model twin of the F5-TTS voice fine-tune; possibly distilling the reliability behaviors *into* the model so scaffolding lightens.

**Endgame is the FRAMEWORK, not this app.** The endgame is the framework's
*general* ability to take any task (protocol + eval rubric + data) and produce a
token-free, local, owned specialist that's genuinely good at it — for the everyday
person, free of Big Tech. Guided imagination is **instantiation #1**: the first
proof and the vehicle for discovering the framework. (Earlier wording that called
"a guided-imagination specialist" the endgame was a slip — corrected.) Why it's not
a vanity project: small + scaffolded + fine-tuned + *owned* beats big + cloud +
rented *for a focused task* — and the framework makes that repeatable for ANY task. Open intellectual risk to test, not assume: distillation's best evidence is on *verifiable* tasks (math/code/reasoning — DeepSeek-distill); distilling *subjective creative quality* (immersion) is less proven. The DeepSeek market panic was wrong for the labs but right for the individual — small+efficient+open is more than enough for personal use.

**Open choice (deferred to Phase 2):** dataset-gen teacher = large *open* models only (fully on-thesis) vs. a frontier model for richer seed data (one-time/offline; resulting model still owned). Lean open-only; frontier-seed only if quality demands it.

---

## 2026-05-29 — Evidence course-correction: structured generation, NOT a companion chatbot

Verified capability research (what small local models are *demonstrably* good at) forced an honest correction to the product framing.

**What the evidence says** (high confidence): a small model **specialized (fine-tuned/distilled) for a narrow, well-defined task matches or beats the frontier generalist** at it — e.g. LoRA Llama-3.1 8B at 90% clinical extraction beat zero-shot GPT-4 (86%) and a human (82%) on a desktop GPU with ≤100 examples. Strong, replicated. Apple ships its on-device ~3B model explicitly **"not as an open-ended chatbot"** — scoped to summarize/rewrite/extract/triage. *Requires* fine-tuning; out-of-the-box small models do not beat frontier.

**What it says NOT to build:** an open-ended **empathetic companion/therapist** on a small local model — frontier Claude won **75%** of empathy head-to-heads (EMNLP 2025); small is "good enough to engage," not parity. Also out: broad knowledge, multi-step reasoning, big coding, long context.

**The correction:**
- DROP the (unproven, likely false) framing "small local model = warm empathetic companion."
- The **Imagination Engine is STRUCTURED GENERATION, not a companion chatbot.** Its architecture (classify → bind scene bible → staged beats → assemble, + planned fine-tuned specialist) IS the specialization move the evidence rewards — it moves the task from the "small loses" zone (open empathetic chat) into the "small wins" zone (structured specialized generation). The scaffolding is the strategy, not a crutch.
- The consumer catalog biases toward **structured private experiences**, away from "a private chatbot friend."
- Most defensible public claim: *a small model you run privately, specialized for one task, matches the frontier at that task — fraction of the cost, nothing leaves your device.*

**Test, don't claim:** the losing-empathy study is clinical support (model supplies empathy); our use facilitates the user's own imagining via a structured script — possibly a friendlier spot, but unproven. Validate via generated scripts + user testing, not assertion. (Full evidence: internal capability research doc.)

---

## 2026-05-29 — Scene-binding VALIDATED (PR #2); a near-miss caught

**A silent-dead-feature near-miss, then a real fix.** Scene-binding (PR #2) shipped non-functional: a diagnostic found the classifier returned `archetype=''` on every case, so binding never fired and the generator silently fell back to the old improvise path. Root cause: the archetype instruction was appended *after* the authoritative JSON schema block, so Qwen followed the schema (which omitted `archetype`) and ignored the addendum. Fix: put `archetype` IN the schema as a required key + a labeled ARCHETYPE LIST with mapping hints. Verified 4/4 (Taylor→backstage-pre-show, retire→retire-young, calmer→different-personality, shore→place-deep). **Lesson reinforced: validate a feature actually fires before building on it** — Sonali's "where are we on the 100?" is what surfaced it; we nearly built the roadmap on a dead feature.

**End-to-end validation (Qwen, scene-binding live) on the two worst prior drift cases:**
- **different-personality.** OLD (improvise) drifted onto an unrelated *stage with a microphone and audience* + leaked example anchors verbatim. NEW (bound) held the bible's scene exactly: party-in-your-apartment, breath low, wide stance, unmanaged half-smile, held pause, unclenched jaw. Drift gone. (2204w vs old rambling.)
- **retire-young.** OLD drifted to a generic sunrise-porch-birdsong postcard (the AI "peaceful" default) that missed the actual wish. NEW hit the bible's real anchors: phone face-down / coffee gone cold / years on-call dissolving / the unclaimed day — captured the *emotional core* (time + freedom from obligation), not generic calm.
- Taylor (non-discriminating control: the bare model already knew backstage-Eras) came out tighter but similar — expected.

**Verdict: task-pack #1 architecture is real** — a hand-curated scene bound into a small local model produces the intended experience instead of drifting. This is the keystone the "curated suite" roadmap rests on. Caveat: validated as TEXT and as structural on-scene-ness; whether scripts are genuinely *moving* is a taste call (Sonali) and ultimately an audio judgment (later). PR #2 merged.

**Known small follow-ups (non-blocking):** classifier occasionally leaks the archetype name into `subject` for unnamed-subject cases; structured-output repair still misses some unescaped inner-quote cases (intermittent parse fail). Harden later.
