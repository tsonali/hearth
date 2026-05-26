# Imagination Engine

A local-first, private desktop app that generates personalized guided-imagination audio sessions. v0 builds one protocol: **future-self visualization**.

Everything runs on the user's own machine. No cloud inference, no token meter, no server, no telemetry. Built on open-source primitives (MLX, Llama 3.1 8B, FastAPI, SQLite, Piper) — no third-party orchestrators.

## Project layout

- **`CLAUDE.md`** — Standing context for Claude Code. Read every session. Encodes principles and scope so the project doesn't drift.
- **`build-plan/`** — The week-one build, broken into numbered tasks. Work them in order.
- **`protocols/future-self-visualization.md`** — The protocol design: what a good future-self session contains, structurally. Source of truth for session quality.
- **`docs/decisions-log.md`** — Running log of decisions and their reasoning. Append whenever something changes.
- **`docs/vision.md`** — The longer-horizon picture. Kept separate from v0 so it doesn't contaminate the build.
- **`src/imagination_engine/`** — The application itself.
  - `inference.py` — local model engine (MLX-LM wrapper, our owned layer)
  - `server.py` — FastAPI app on loopback
  - `web/` — single static HTML + CSS for the v0 shell
  - `config.py` — paths, model id, server defaults
  - `__main__.py` — CLI entry (`serve` / `probe`)

## Running it

Requires macOS on Apple Silicon and [uv](https://github.com/astral-sh/uv).

```sh
# One-time setup: create the venv and install dependencies
uv sync

# Smoke test inference from the CLI (downloads the model on first run, ~4.5 GB)
uv run imagination-engine probe "Say hello in one short sentence."

# Run the local server
uv run imagination-engine serve
# then open http://127.0.0.1:8765
```

Once the model is cached locally, the app runs fully offline.

## The one rule

Build the one template, concretely, end to end. Do not build the "platform" first. The flexible engine is extracted later, from real templates. Concrete first, abstraction second.
