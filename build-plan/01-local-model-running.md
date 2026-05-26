# Task 01 — Get a local language model running and talking to a bare app

**Goal:** Prove the foundation. A local language model runs on the founder's machine, with zero network calls, and responds to typed input inside a minimal app shell.

## Why this is first
Everything else depends on local inference working. Before building anything user-facing, prove the engine turns over: text in, text out, fully offline, no token meter. If this works, the central architectural bet is validated.

## What to build
- A minimal desktop app shell (whatever framework Claude Code recommends for an Apple Silicon Mac target — keep it simple).
- A local language model running on-device. Choose a small, capable model that runs comfortably on Apple Silicon. Claude Code should recommend a specific current option and a local runner to load it.
- A bare text box: founder types a message, the local model responds, response appears. No styling, no features.

## Definition of done
- Typing a message and getting a coherent response from a model running entirely on the local machine.
- Network can be fully disabled and it still works.
- The founder has confirmed it runs at acceptable speed on her actual machine.

## Notes
- Ugly is fine. This is a proof, not a product.
- If model speed is poor, try a smaller model before doing anything clever. Log the model choice and reasoning in `docs/decisions-log.md`.
