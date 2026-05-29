# Strategy — the privacy-native local-AI bet

This document is the north star. It records *why* this project exists beyond
the app itself, and the sequence we're committed to. Updated when the
strategy changes; see `decisions-log.md` for tactical decisions.

---

## The thesis

The biggest AI labs have a structural blind spot, and it is not an accident —
it is their P&L. Their business is metered cloud inference. Every query that
runs on your own machine is revenue they do not collect. So they have a
permanent incentive *against* local-first, private-by-construction AI.

That leaves a category wide open: **purpose-built applications whose entire
value proposition is that nothing ever leaves the device.** Not "chat with a
local model" shells (Ollama, LM Studio, Jan) — those hand you a model and a
text box. Applications. For the things you would never type into a cloud
chatbot: your imagination, your grief, your ambitions, your inner life.

The Imagination Engine is the first proof of that thesis in running code.

The mission, stated plainly: **give the everyday person capable, genuinely
private AI they own and run themselves — and unshackle them from Big Tech AI
(Meta, OpenAI, Anthropic / the "Claudes" included).** Independence, not just
privacy.

**The endgame is the FRAMEWORK, not any one app.** The destination is a
*generalizable* framework that takes any task — its protocol, its eval rubric,
its data — and produces a token-free, local, owned model that's genuinely good
at it, so a regular person can do *whatever they want* with private AI. The
**Imagination Engine is instantiation #1**: the first proof, and the vehicle for
discovering what the framework actually is. Guided imagination is one task plugged
into the framework — never the goal itself. (Watch for slippage: whenever a plan
reads as "the endgame is [this app/task]," it's wrong — the endgame is the
general capability.)

**A separate layer — keep it separate.** Sonali's books (*God in the Machine*,
*Unreality*) target **AI's dishonesty about its own nature** — claiming unearned
authority, refusing to admit it's unreal, posing as your friend. The Imagination
Engine *product* answers that: an instrument, not a companion. But this is her
**personal / authorial stance, NOT a property of the framework.** The technology
is agnostic — someone could build a companion on it and it would still be the
framework. Keep the technology (for everyone) and the philosophy (hers, in her
product) cleanly separate. Welding them together was an earlier mistake.

## The position: democratize private AI

The ownable position is not "privacy-native local AI" in the abstract — it's a
**technical solution that lets the everyday person own capable private AI,
independent of Big Tech.** Its defining pillars are all technical/access:

1. **Private & local** — runs entirely on the user's device; nothing leaves it.
   Privacy as architecture, not a setting.
2. **Anti-token, anti-massive-model** — no per-token metering, no account,
   own-don't-rent; *small* models on the user's own hardware, not frontier giants
   in someone's datacenter. Independence from the metered-cloud economy.
3. **Small-model reliability scaffolding (the enabler)** — staged generation +
   on-device task-specific evals + fine-tuning: what makes a small local model
   actually good enough that a normal person would *choose* it. A verified scan
   found this layer unpackaged anywhere, none targeting Apple's MLX — so it's the
   IP, not a workaround. Endgame: a distilled, *owned* specialist model (see the
   model roadmap in `decisions-log.md`).

The intersection — *usable* private AI for regular people, free of the token game —
is the empty, ownable space. (Anti-anthropomorphism is **not** a pillar here; it's
the product's / author's separable stance, above.) Competitive detail kept internal.

## What the gap actually is

Not "local models can't do awesome things" — the open-weight frontier (Qwen,
Mistral, DeepSeek, Gemma, Llama) is strong, and a well-chosen 14–32B model
does real work. A local model will never match a frontier *cloud* model at
general intelligence, so the winning shape is **narrow + scaffolded +
private**: one focused task done extremely well, wrapped in enough structure
to punch above the model's raw weight.

The scarce thing is the **scaffolding**, not the weights. Three underserved
layers:

1. **The last mile** — turning models + runners into something a normal
   person double-clicks and uses. Unsolved for almost everything.
2. **Privacy-native product categories** — where local-first is constitutive,
   not a nice-to-have.
3. **Reliability scaffolding for small models** — patterns that make an 8–14B
   model trustworthy at a specific task.

## The sequence (not parallel — this ordering *is* the strategy)

1. **App.** Ship the Imagination Engine as the canonical working radical
   privacy-native artifact. Clean, decoupled seams (see "framework north
   star" below) so later extraction is a lift, not a rewrite.
2. **Essay.** Frame the thesis once the artifact has earned it. A manifesto
   without a great working thing is just another AI-take; the artifact
   amplifies the essay and cannot substitute for it. Ship first, theorize
   second.
3. **Framework.** Extract the reusable scaffold — but only after a *second*
   privacy-native app proves which patterns generalize. Premature abstraction
   (one example masquerading as general) is the named trap. This is Phase 2+.

The plays were pressure-tested. What survived: be early to a real-but-nascent
category and hold conviction through the quiet; let execution quality earn the
thesis; resist extracting a framework from a single example. The deepest trap:
optimizing for influence corrupts the product (visibility over quality,
breadth over depth). Influence is a *byproduct* of an undeniable artifact,
never a direct target.

## Framework north star (build the seams clean now; extract later)

Strip the app down — what is true of *any* private local-AI app?

- **Model-swappable inference seam** — one `Engine` interface over MLX /
  llama.cpp; swap models without touching app logic. (`inference.py`)
- **Loopback app shell** — FastAPI on `127.0.0.1`, single static page,
  offline-by-construction, zero telemetry. Privacy as architecture.
- **Structured-generation decomposition** — never ask a small model for the
  whole artifact at once; *classify → plan → bounded staged sub-calls →
  assemble*, each call with one concrete target. The transferable IP.
- **Eval harness** — mechanical floor + strict LLM-judge rubric + model A/B
  tooling. "How to know if your local output is actually good."
- **Local memory + trust primitives** — on-device SQLite; offline-verifiable
  ("turn off wifi"); 0-bytes-transmitted proof.

Domain-specific (stays in the app): the immersion protocol, scene bibles, the
voice rules.

Eventual developer pitch: *bring your protocol, your prompts, your eval
rubric; get a private, offline, model-swappable desktop AI app with the
reliability scaffolding already solved.* "Rails for privacy-native local-AI
apps." Extracted after app #2 — not before.
