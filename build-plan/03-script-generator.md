# Task 03 — Build the visualization script generator

**Goal:** Take the structured intake summary and generate a personalized, well-paced future-self visualization script.

## Why
This is the heart of the product, and where the founder's *Unreality* expertise becomes product logic. The model does not freestyle a session — it personalizes *within* a protocol scaffold defined by the founder. The scaffold ensures every session has the right structure; the model fills it with the user's specifics.

## What to build
- A generation step that takes the intake summary and the protocol scaffold from `protocols/future-self-visualization.md` and produces a complete script.
- The script must follow the protocol's structure: an opening settle / induction, the visualization body, and a clear, gentle return / re-orientation at the end.
- The script is written in the protocol's voice: second person, present tense, paced for spoken delivery with natural pauses, calm.
- Output should be plain text marked up enough that Task 04 (voice) can pace it correctly — agree a simple convention with the founder for indicating pauses.

## Definition of done
- Given a real intake summary, the generator produces a script the founder reads and judges as a genuinely good guided session — correctly structured, personalized, well-paced, with a proper return at the end.
- The opening and especially the **return/re-orientation** are reliably present. The session must always bring the user back.

## Notes
- The protocol scaffold is the source of truth. If the model's output drifts from it, fix the scaffold or the prompt — do not let the structure be optional.
- Pacing matters enormously for spoken delivery. Err toward slower, more spacious.
