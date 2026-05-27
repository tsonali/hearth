# Imagination Engine

A local, private tool for guided imagination. You describe what you want to imagine — anything — and the engine produces a calm, paced audio session in *your own voice*. You close your eyes and listen.

Nothing ever leaves your machine. There is no server, no account, no telemetry. The language model runs on your laptop. The voice model is one you train on your own recordings. The audio is rendered locally and played in your browser.

> By [Sonali Maitra](https://sonalimaitra.com) — author of *God in the Machine* (on AI and unwarranted authority) and the in-progress *Unreality* (on how AI-generated content blurs real and simulated experience). This product is that work made operational: a private place to do the imagining you wouldn't share with anyone else, in a voice you trust because it's yours.

---

## What it does

You open the engine in your browser. You type — in your own words — what you want to imagine. Anything: yourself a year from now succeeding at something hard, being a different character entirely, your life if you'd taken another path, being Lincoln the night before Gettysburg, being Taylor Swift backstage. *Anything legal.*

The engine has a short, warm conversation with you to pick up sensory specifics — where, when, what does it feel like in the body. Then it builds you a 10–15 minute guided session and reads it to you, in your own voice, with real pauses between paragraphs so the imagery has time to land.

After, you go live your day.

---

## Why local-only

Every part of this product is built on the assumption that **what you imagine is your business and no one else's**. So:

- **The language model runs on your machine.** No API calls to OpenAI, Anthropic, or anyone else. Llama 3.1 8B (open weights) running locally via [MLX](https://github.com/ml-explore/mlx) on Apple Silicon.
- **The voice model is yours.** You record ~30 minutes of your own voice; the engine fine-tunes a local copy of [F5-TTS](https://github.com/SWivid/F5-TTS) on it. The trained model never leaves your machine.
- **The audio is rendered locally and played in-browser.** There is no audio file you can download, share, or upload. The session plays, then it's gone.
- **No account. No email. No sign-up.** There is nothing to leak because nothing exists about you anywhere.
- **No telemetry, ever.** Not "anonymized analytics." Not "crash reports." Nothing. The engine does not know who you are or what you did with it.

**You can verify this yourself.** Once the engine and your voice model are downloaded, turn off your WiFi. The engine keeps working, end to end. If anything required the network, it would fail at that point. It doesn't.

You can also read the code. That's why it's open source.

---

## Status

This is a working v0 in active development. Currently:

- ✅ Local LLM (Llama 3.1 8B via MLX) — running, with proper sampling controls
- ✅ Intake conversation — warm, brief, sensory; user-paced (skip whenever you want)
- ✅ Script generator — multi-stage (settle → imagining → return), produces ~12-minute immersive sessions
- ✅ Audio render — Kokoro TTS for the placeholder voice; F5-TTS for the user's own cloned voice
- ✅ Recording app — drives the user through ~200 sentences to produce training data for their own voice model
- ✅ Voice fine-tuning pipeline — runs on Apple Silicon (M-series Mac)
- 🚧 Distribution — manual install today; signed/notarized website download soon
- 🚧 Memory & reflection layer — short post-session prompts stored locally
- 🚧 Beta — currently single-user (the author's machine)

This is not a polished consumer app yet. If you're not comfortable running a Python project from a terminal, wait for the packaged release. If you are, the install steps are below.

---

## Install (development build)

Requires an Apple Silicon Mac (M1 / M2 / M3 / etc.) running macOS 13 or later.

```bash
# 1. Clone the repo
git clone https://github.com/tsonali/imagination-engine.git
cd imagination-engine

# 2. Install uv (Python project manager — Apache-2.0 / MIT)
curl -LsSf https://astral.sh/uv/install.sh | sh

# 3. Sync the Python environment (installs MLX, FastAPI, F5-TTS, Kokoro, etc.)
uv sync

# 4. Install ffmpeg (used by the F5-TTS training stack)
brew install ffmpeg

# 5. Start the local server
uv run imagination-engine serve

# 6. Open the engine
# In your browser, go to http://127.0.0.1:8765/intake
```

The first time you generate a session, the engine downloads the LLM weights (~4.5 GB) and the voice model weights (~1.5 GB). Once cached, everything runs offline.

To train your own voice (so the engine speaks in your voice instead of the placeholder), see `docs/voice-training.md`.

---

## The stack, by license

Everything in this project is open source. The runtime depends on:

- **[Llama 3.1 8B Instruct](https://huggingface.co/meta-llama/Meta-Llama-3.1-8B-Instruct)** — Meta, Llama 3.1 Community License (open weights)
- **[MLX / mlx-lm](https://github.com/ml-explore/mlx-lm)** — Apple, MIT
- **[F5-TTS](https://github.com/SWivid/F5-TTS)** — MIT, for voice cloning + fine-tuning
- **[Kokoro TTS](https://github.com/hexgrad/kokoro)** — Apache-2.0, used as the placeholder voice
- **[FastAPI](https://fastapi.tiangolo.com)** — MIT, the local HTTP server
- **[Inter](https://rsms.me/inter/)** / **[Archivo Black](https://fonts.google.com/specimen/Archivo+Black)** — both Open Font License, bundled locally
- **SQLite** (coming) — public domain, for the local memory layer

The product code itself is MIT-licensed. See [`LICENSE`](LICENSE).

---

## A note from the author

Most AI tools want to know what you're thinking — that's the business model. This one is the opposite: it exists *because* what you're thinking is no one else's business, including ours. The privacy isn't a feature. It's the architecture. The whole product would fall apart if any of it called home, so none of it does.

If that's the kind of tool you want to use — or build with — read the code and tell me what you think.

— Sonali Maitra
