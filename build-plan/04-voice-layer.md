# Task 04 — Add the voice (local text-to-speech)

**Goal:** Render the generated script to a calm, warm, well-paced guided-audio session that plays inside the app — all locally.

## Why
Audio-led, internally-imaged delivery is the correct modality for this product: the user listens with eyes closed and renders the imagery themselves. Voice is also the modality where high-quality, on-device, zero-marginal-cost generation is genuinely achievable today.

## What to build
- Integrate a local neural text-to-speech engine. Claude Code should recommend a specific current option that runs well on Apple Silicon and produces a natural, calm voice.
- Wire the script (from Task 03) through TTS so it plays as audio in the app.
- Honor pacing: the pause convention from Task 03 should translate into real silence in the audio. A guided session lives or dies on pacing — pauses must be real and generous.
- Basic playback controls: play, pause, stop.

## Definition of done
- A full future-self session plays end to end as audio, on the founder's machine, fully offline.
- The voice is calm and warm enough that the founder would actually use it for a real session.
- Pauses are real and the pacing feels spacious, not rushed.

## Notes
- Voice quality and pacing are the difference between "this works" and "this is unusable." Spend time here.
- If the TTS voice options are all too flat or robotic for guided imagery, log it in the decisions log and discuss with the founder before moving on — this is a make-or-break quality bar.
