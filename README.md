# Hearth

### Private AI that lives in your house and never leaves it.

Most AI runs on someone else's computer: your data goes to a company, and you pay by the use forever. Hearth is the opposite. Small models have gotten good enough to run privately on an ordinary laptop and still be genuinely useful — so this is a set of focused tools that do exactly that, given away in the public domain. **→ [Read the reasoning](MANIFESTO.md).**

Hearth is a growing suite of focused, private tools — and the means to build your own:

- 🧘 **Imagination Engine** — guided sessions in *your own voice*, you close your eyes and imagine.
- ✍️ **The Secretary** — drafts, replies, summaries, rewrites, action items — on your words, in your voice, never uploaded.
- 🪞 **Honest companion** — a reflective mirror that helps you think; it refuses to pretend it's your friend.
- 📂 **Ask your own files** — point it at your notes/docs and ask; it answers from what's there, says so when it isn't, sends nothing anywhere.
- 🛠️ **Build your own** — describe an instrument, point it at your data, keep it. Yours, on your machine.

Everything runs on a small model on your laptop. Released into the **public domain** ([CC0](LICENSE)) — no attribution, no strings.

> By [Sonali Maitra](https://sonalimaitra.com) — author of *God in the Machine* (on AI claiming an authority over us it hasn't earned) and the in-progress *Unreality* (on the human power to *enter* unreality as one of our greatest gifts — and the danger of AI that won't admit its own). This is both arguments made operational.

> **Status — honest:** real, working software under active development — a beta, not a polished product. All five tools run locally today, and there's a [double-click install](#install) (download, unzip, double-click; macOS will ask you to right-click → Open the first time, because the app isn't notarized yet).

---

## The bigger bet

Hearth is the first proof of a thesis: the largest AI companies have a structural blind spot — their business is metered cloud inference, so they have a permanent incentive *against* software that runs privately on your own machine. That leaves a whole category open: **purpose-built applications whose entire value is that nothing ever leaves the device** — for the things you'd never type into a cloud chatbot.

The specific position is a **three-way intersection almost nobody combines**: *fully local* (offline by construction), *small-model reliability scaffolding* (the engineering that makes a small on-device model punch above its weight), and *honest anti-anthropomorphism* (an instrument, never a fake friend). Each alone is partly occupied; the intersection is open.

The Imagination Engine is step one. The plan, in order:

1. **Ship this app** as the canonical working privacy-native artifact.
2. **Write the essay** that frames why it matters — *after* the artifact has earned it.
3. **Extract the framework** underneath it — the reusable scaffold for private, offline, model-swappable AI apps — but only once a second app proves what actually generalizes.

The full reasoning, and the traps we're steering around, are in [`docs/strategy.md`](docs/strategy.md). We're building this in the open on purpose: goal stated up front, every step shown and explained. If *"don't trust me, read the code"* is the promise, the repository itself has to be legible — so it is.

---

## Why local-only

Every part of Hearth is built on the assumption that **what you do here is your business and no one else's**. So:

- **The model runs on your machine.** No API calls to OpenAI, Anthropic, or anyone else. A small open-weight model (currently Qwen 2.5 14B) running locally via [MLX](https://github.com/ml-explore/mlx) on Apple Silicon.
- **Nothing is uploaded.** No account, no email, no sign-up, no telemetry, no "anonymized analytics," no crash reports. There is nothing to leak because nothing about you exists anywhere.
- **You can verify it.** Once the model is downloaded, turn off your WiFi — Hearth keeps working, end to end. If anything required the network, it would fail at that point. It doesn't.

You can also read every line of code. That's the point.

---

## Status — honest

Working software, in active development. The engines for all four tools run locally
today (see `docs/roadmap.md` and `docs/own-model-plan.md` for the live plan):

- ✅ **Imagination Engine** — intake → staged script generation → audio in your own voice
- ✅ **The Secretary** — draft / reply / summarize / rewrite / extract / organize, with tones and your own voice-style
- ✅ **Companion** — honest reflective companion (+ cross-session memory)
- ✅ **Ask Your Files** — local RAG: index your files, ask, grounded answers that refuse to hallucinate
- ✅ **Build Your Own** — describe an instrument (optionally ground it on a folder), keep it; full UI at `/build`
- ✅ **Double-click app** — download the zip, double-click `Start Hearth.command`; no terminal needed
- 🚧 **Our own fine-tuned model** — trains locally, already better than base and improving each cycle (see `docs/own-model-plan.md`)
- 🚧 **Signed/notarized installer** — today macOS asks you to right-click → Open the first time; a notarized `.dmg` is coming

Honest residual: it's a beta. The first model download is ~8 GB, sessions take real minutes to render, and it wants an Apple Silicon Mac. Everything else works today.

---

## Install

Requires an Apple Silicon Mac.

### Easiest — double-click
1. [Download the repo](https://github.com/tsonali/hearth) (green **Code → Download ZIP**), unzip it.
2. Double-click **`Start Hearth.command`**.

First run installs everything and does a one-time ~8 GB model download, then opens Hearth
in your browser. After that, double-clicking just starts it. Everything runs on your
machine; nothing is uploaded. *(macOS may ask you to confirm opening a downloaded script —
right-click → Open the first time.)*

### Manual (development build)

Core install needs no TTS (generation + the tools); add `--extra voice` for audio.

```bash
# 1. Clone
git clone https://github.com/tsonali/hearth.git
cd hearth

# 2. Install uv (Python project manager)
curl -LsSf https://astral.sh/uv/install.sh | sh

# 3. Sync the environment (core: generation + companion + ask)
uv sync                  # add: uv sync --extra voice   (for audio/TTS)

# 4. Start Hearth
uv run imagination-engine serve

# 5. Open it
# http://127.0.0.1:8765   (the Hearth hub — all the tools)
```

The model weights (~8 GB) download once on first use, then everything runs offline.

---

## The stack, by license

Hearth's own code is **public domain (CC0)** — no attribution, no strings. It builds on:

- **[Qwen 2.5 14B Instruct](https://huggingface.co/Qwen)** — Alibaba, Apache-2.0 (the local model)
- **[MLX / mlx-lm](https://github.com/ml-explore/mlx-lm)** — Apple, MIT
- **[FastAPI](https://fastapi.tiangolo.com)** — MIT, the local HTTP server
- **[SQLite](https://sqlite.org)** — public domain, the local memory + RAG store
- **Voice (optional `--extra voice`):** [Kokoro](https://github.com/hexgrad/kokoro) (Apache-2.0) and [Chatterbox](https://github.com/resemble-ai/chatterbox) (MIT) for shippable voices; [F5-TTS](https://github.com/SWivid/F5-TTS) (code MIT, weights CC-BY-NC) used non-commercially for the personal voice-clone
- **[Inter](https://rsms.me/inter/)** / **[Archivo Black](https://fonts.google.com/specimen/Archivo+Black)** — Open Font License, bundled locally

**The code in this repo is released into the public domain (CC0) — no copyright, no attribution required, no strings.** Take it, fork it, build on it, ship it; you owe nothing. This is deliberate: the project exists to give people access that profit-seekers withhold, and functional code shouldn't be locked up by copyright at all. See [`LICENSE`](LICENSE). (Third-party dependencies keep their own licenses; nothing here is or will be sold.)

---

## Follow the work

This repo is built to be **read**, not just run. The goal and every step are documented as a narrative spine you can traverse:

- [`docs/strategy.md`](docs/strategy.md) — the ultimate goal and the sequence to reach it.
- [`docs/decisions-log.md`](docs/decisions-log.md) — *why* every architectural turn was taken, with the reasoning and the data behind it (including the dead-ends — those are part of the honesty).
- [`docs/daily-log.md`](docs/daily-log.md) — the day-by-day grind: what moved, what the numbers said, what's next.

Commit messages explain the *why*, not just the *what*. Code comments at the seams explain the reasoning, not just the mechanism. **The code shows; the prose woven through it tells.** Read it top to bottom and you can follow both the engineering and the intent.

---

## A note from the author

Most AI tools want to know what you're thinking — that's the business model. This one is the opposite: it exists *because* what you're thinking is no one else's business, including ours. The privacy isn't a feature. It's the architecture. The whole product would fall apart if any of it called home, so none of it does.

If that's the kind of tool you want to use — or build with — read the code and tell me what you think.

— Sonali Maitra

---

## How it's built — and how it gets better

Hearth runs on a small open model (Qwen 2.5 14B, 4-bit) on your own machine via MLX —
no cloud, no API, no metering. The four tools are thin, honest layers over that one
local model; each is driven by a system prompt, not a separate service.

**Our own model.** We fine-tune a specialist with LoRA, **locally** (it trains on an
Apple-Silicon Mac for $0 — nothing leaves the house, true to the whole premise). Why
fine-tune at all? Not to be "smarter" than the base — to be *reliably* the right kind of
thing: vivid and concrete for guided sessions, an honest non-prescriptive mirror for the
companion, clean and preamble-free for the secretary.

**The method — taste, mechanized.** The hard part isn't the code; it's teaching the model
what *good* means. So:
1. A small set of genuinely-good human exemplars sets the bar.
2. The model generates many candidates across diverse prompts.
3. They're **curated** against an explicit quality bar (concrete physical detail, no
   AI-y abstraction, no preachy intros, no fake warmth) — the founder's taste, written
   down as rules.
4. We train on the survivors, evaluate base-vs-tuned by *reading the output*, and repeat
   until it plateaus.
The training corpus itself is **never redistributed** — training on material is fair use,
republishing it is not, so it stays off this repo. We ship the model and the method, not
other people's data.

**The honest state:** the local fine-tune is measurably better than the base model and
improving each cycle — *good, not magic*. The full reasoning, every decision, and the
candid results live in [`docs/`](docs/) (start with `decisions-log.md`).
