# Task 05 — Add local memory and reflection capture

**Goal:** After a session, capture a short reflection from the user, store the whole session locally, and prove the loop — a later session that references an earlier one.

## Why
The product's value compounds over time. A session in week three should know what happened in week one. That accumulated, structured, *local* history is both the user value and the switching cost — and because it never leaves the device, it costs the user nothing in privacy.

## What to build
- After audio playback ends, a brief reflection prompt: how did that land, what came up, did anything shift. Keep it short and optional.
- A local database storing, per session: the intake summary, the generated script, the reflection, and a timestamp.
- Feed prior sessions back in: when a returning user does intake, the engine should be aware of their history and able to reference it naturally ("last time you worked on X — is this related, or something new?").

## Definition of done
- A session, with reflection, is stored locally.
- A second session demonstrably references the first — in the intake conversation and/or the generated script.
- All storage is local. Confirm nothing is transmitted.

## Notes
- Structured memory, not raw transcript-stuffing. Store discrete fields so the engine can reference history efficiently without re-feeding everything.
- This completes the v0 loop: talk → generate → speak → reflect → remember. At this point the founder has a rough but whole product to use and judge.
