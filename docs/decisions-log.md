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
