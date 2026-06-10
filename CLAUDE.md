# CLAUDE.md — Imagination Engine

> ## ▶ RESUME HERE (new session): read **`HANDOFF.md`** first, then run its status checks.
> It captures EXACTLY where we are, what's running on the mini (recursive trainer +
> caffeinate, both survive restarts), and the next autonomous actions. Working style:
> act autonomously, don't over-ask, be honest, test test test, keep the mini busy.
> Hearth is now a working v0 on our OWN model; the loop is: improve model → fold in → re-QC.

This file is read automatically at the start of every Claude Code session. It is the standing context for the project. Keep it current; when an architecture decision changes, update this file and add an entry to `docs/decisions-log.md`.

---

## What this project is

A local-first, privacy-first desktop application that generates personalized **guided imagination sessions** as audio. The user has an open conversation about something they want to work toward; the app generates a personalized, paced visualization script; local text-to-speech renders it to a calm guided-audio session; the user listens with eyes closed and does the imagining themselves; the app captures a short reflection afterward and remembers it.

**v0 is one universal scaffold, not one template.** The protocol shape is `settle → user's chosen imagining → return → reflection`. The intake conversation is open-ended: the user describes what they want to imagine (themselves succeeding, being a different character, their life differently, being a real or fictional figure — anything). The same architectural shape produces the session; the content is the user's. See `docs/decisions-log.md` entry "Scope reframe: imagination engine, not future-self engine" (2026-05-26).

This is still "build concrete, abstract later" — one protocol scaffold, built concretely. We just no longer pretend it only serves future-self visualization. Trauma- / grief- / exposure-adjacent protocols with different safety profiles remain deferred; those would be different *scaffolds*, not different *contents*.

**No content guardrails.** Adults only, small beta. The engine helps people imagine whatever they want. See `memory: project-no-guardrails` and `docs/decisions-log.md`. The single hard floor (sexual content involving minors) is already law and base-model behavior; we don't relax that. Beyond that floor, we don't filter, refuse, or topic-block.

## Founder context

The founder (Sonali) is the product lead, protocol designer, and director — not a software engineer. She is an exceptionally capable director of Claude Code, a former patent litigator, a Stanford Law lecturer, and the author of *God in the Machine* (on AI claiming an authority over us it hasn't earned) and the in-progress *Unreality* (on the human capacity to *enter* unreality as one of our greatest superpowers — and on the real danger being AI that refuses to acknowledge its *own* unreality: pretending to be your friend, inviting anthropomorphism). **Both books target the same thing — AI's dishonesty about its own nature — and the Imagination Engine is wholly consistent with that thesis, not contrary to it:** it is the *honest* harnessing of AI for deliberate, self-aware imagining, in the user's own voice, with no pretense of companionship ("instrument, not companion" is this stance made architecture). The protocol design for this product draws on that body of work. Claude Code does the implementation; Sonali owns product, protocol, and quality judgment.

## Core principles (do not violate without an explicit decision logged)

1. **Local-first.** All inference — language model and text-to-speech — runs on the user's own machine. No cloud model APIs. No token metering. The app should function fully offline after install.
2. **Private by construction.** Nothing the user says, no generated session, no reflection, ever leaves the device. There is no server, no telemetry, no analytics that transmit user content. This is the central trust proposition and the headline of the product. Privacy is not a setting; it is the architecture.
3. **Instrument, not companion.** This is a cognitive tool the user opens to do focused work and then closes to go live their life. The conversation layer exists for *intake* (understanding what to build the session about) and *reflection* (capturing how it landed) — NOT to be an ongoing emotional companion. Design choices that would push the product toward standing companionship are out of scope. Keep it instrumental.
4. **Audio-led, internally-imaged.** The product never generates video or visual imagery of the scene. The imagery happens in the user's mind — that is the therapeutic mechanism. The product generates *words* and *voice*. Text is the thinking layer; voice is the delivery layer.
5. **Build concrete, extract abstractions later.** One template, end to end, even if rough. Resist building a "general engine" before two real templates exist.

## v0 architecture

Three components, all local:

- **Reasoning/protocol layer** — a small language model running on-device. Two jobs: (a) run the open intake conversation, (b) generate the personalized visualization script from the intake summary. v0 may use a capable off-the-shelf small model; a fine-tuned model is a later optimization, not a v0 requirement.
- **Voice layer** — local neural text-to-speech that renders the generated script to a warm, calm, well-paced guided-audio session.
- **Memory layer** — a local database storing each session (intake summary, generated script, reflection, timestamp) so subsequent sessions can reference prior ones.

All wrapped in a desktop application shell. **Target the founder's own machine first (Apple Silicon Mac).** Cross-platform is a later concern — prove it end-to-end on one machine before generalizing.

## What is explicitly OUT of scope for v0

- Any protocol other than future-self visualization
- Any clinical / trauma / grief / exposure protocol
- Cross-platform support
- Model fine-tuning
- A "platform" / multi-template abstraction layer
- Any cloud component, account system, or server
- Companion-style ongoing relationship features
- Distribution / installer polish for non-technical users (prove the build works first)

## Honest difficulty notes

The v0 as scoped is a tractable project — local model runners, local TTS, and a local database are all mature, well-documented building blocks. This is buildable by the founder directing Claude Code.

The genuinely hard work comes LATER, at the platform/scaling stage: making it run reliably on machines that aren't the founder's, packaging multi-gigabyte models for non-technical users, the long tail of edge cases, and the ongoing ownership of a live product that strangers depend on. Those are real and should be met concretely when the project reaches that stage — not pre-solved now.

## How to work in this repo

- The build plan lives in `build-plan/`, broken into discrete numbered tasks. Work them in order.
- When a design or architecture decision is made or changed, append it to `docs/decisions-log.md` with the date and the reasoning.
- Protocol design — the actual structure of the future-self visualization script — lives in `protocols/`. This is the founder's domain; treat it as the source of truth for what a good session contains.
- Prefer the simplest thing that works. This is a v0. Ugly-but-whole beats elegant-but-partial.
