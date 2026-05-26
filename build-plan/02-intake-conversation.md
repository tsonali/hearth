# Task 02 — Build the open intake conversation

**Goal:** A genuine open-ended conversation where the user describes what they want to work toward, and the local model draws it out with good follow-up questions, ending in a structured summary of what the session should be about.

## Why
This is the "specification-removal" principle: the user should not pick from a rigid menu. They should be able to say, in their own words, something like *"I keep spiraling about a hard conversation with my mother on Sunday"* — and the engine takes it from there. The intake is the front door to a session. It is NOT a standing companion relationship — keep it scoped to understanding what to build.

## What to build
- A conversational flow: the model opens, asks what the user wants to work toward, and asks 3–6 thoughtful follow-up questions to get specifics — the situation, the desired future state, what's in the way, sensory and emotional detail.
- The conversation ends by producing a **structured intake summary**: a compact representation of what the future-self session should focus on. Define the fields with the founder (e.g. goal, time horizon, current obstacle, desired feeling, concrete details to anchor on).
- The summary is the handoff to Task 03.

## Definition of done
- A full intake conversation runs locally, feels warm and genuinely curious (not interrogative), and ends with a structured summary that captures what matters.
- The founder has tested it on a real thing she'd actually want to work on and judged the summary accurate.

## Notes
- The quality bar here is the founder's. The follow-up questions should reflect the protocol design in `protocols/future-self-visualization.md` — they exist to gather what a good session needs.
- Keep the conversation bounded. When enough is gathered, move to generating the session. Do not let intake drift into open-ended chat.
