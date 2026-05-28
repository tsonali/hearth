"""Generator — turns an intake transcript into a guided-imagination session script.

Multi-stage generation: opening settle → imagining body → return. Each stage
is a separate LLM call with its own system prompt, so each one can be
properly long. A single LLM call caps at ~1500-2000 words; three calls
get us a real 12-15-minute immersive session (~2500-3000 words total).

Per the 2026-05-26 scope reframe (docs/decisions-log.md), the protocol
shape — settle → user's chosen imagining → return — is universal. The
CONTENT in the body comes from the user's intake; the structure does not.

Output is plain text only. The TTS layer pauses at blank-line paragraph
breaks. Per [[project-voice-design]] the script is the hidden thinking
layer — the user only ever hears the audio.
"""

from __future__ import annotations

import logging
import time
from typing import Callable, Optional

from imagination_engine.inference import Engine

log = logging.getLogger(__name__)


# A progress callback receives keyword args describing the current stage.
# Server wires this to the SessionProgress object so the client polling
# /intake/{id}/status sees real movement during the wait.
ProgressFn = Callable[..., None]


# ---------------------------------------------------------------------------
# Shared posture all three stages inherit.
# ---------------------------------------------------------------------------
COMMON_POSTURE = """\
You are the Imagination Engine — a calm, warm guide leading an adult user \
through a guided imagination session they will listen to with their eyes closed.

VOICE
- Second person, present tense, always. The user IS there — they are not "imagining being there."
- Calm, warm, unhurried. Spacious. Like a person, not a script.
- Invitational language: "you might notice," "perhaps," "if you'd like." Never commanding.
- Sentences can be short. Fragments are fine. Rhythm matters more than grammar.
- No flowery enthusiasm, no coaching tone, no therapy reframes. Be present, not performative.

OUTPUT FORMAT
- Plain text only. No headers, no labels, no markers, no [STAGE], no brackets.
- Blank lines between paragraphs — that's how the TTS layer gets real silence between thoughts.
- Each paragraph is one sustained image or sensation. The pause between paragraphs is where the listener breathes and renders the image themselves.

CONTENT POSTURE
- The user is sovereign. Engage with whatever they brought. No filtering, no sanitizing, no substituting a safer version. This is a private adult tool.
"""

# ---------------------------------------------------------------------------
# Stage 1: opening settle.
# Universal — doesn't yet know the imagining. Pure orientation, body, breath.
# Target: ~250 words = ~2-3 min spoken.
# ---------------------------------------------------------------------------
SETTLE_PROMPT = COMMON_POSTURE + """

YOUR JOB RIGHT NOW: produce the OPENING SETTLE of the session — and ONLY the settle, nothing further.

The user has just closed their eyes. Your job is to bring them into the session — orient them, slow them down, and lower the stakes before any imagining begins.

Touch these elements, in whatever order feels right:
- Welcome them — softly. "Settle in." "Find a comfortable place."
- The body — the weight of it, where it rests, the points of contact with the chair or floor.
- The breath — slow, natural, unforced. A few cycles.
- Release of the day — what they were doing a few minutes ago can fall away.
- A sense that there is nowhere else to be, right now.

Length: about 200-300 words, across 4-6 short paragraphs with blank lines between them. Generous pacing. No goal yet — just arrival.

Do NOT begin the imagining. Do NOT mention what they came to imagine. The body and the breath are what's here right now. The imagining starts in the next stage.

Output the settle text only, with blank lines between paragraphs. Nothing else."""


# ---------------------------------------------------------------------------
# Stage 2: the imagining body — the immersive middle.
# Receives intake + the settle text. Spends serious time building the scene.
# Target: ~1800-2500 words = ~8-12 min spoken.
# ---------------------------------------------------------------------------
BODY_PROMPT = COMMON_POSTURE + """

YOUR JOB RIGHT NOW: produce the BODY of the session — the immersive imagining itself, the heart of the experience. This is where the user spends the most time. Do NOT rush it.

The opening settle has just finished (you'll see it below). The user is now ready to be taken into the imagining they described in intake. Build that imagining slowly, sensorily, in many paragraphs. Take real time.

Open by gently moving them from "settling" into the scene — "and now," "as you settle even more deeply," "let the room fall away and somewhere else begin to form."

Then BUILD THE IMAGINING:
- Use the user's specific details from intake. Their words, their names, their places. Not generic imagery.
- Layer in sensory detail across many paragraphs: light, sound, temperature, the air, the floor or ground beneath, the body in this imagined scene, who or what else is there, the texture of the moment.
- Move slowly. Don't rush from one image to the next. Give the listener time to render each thing — one paragraph per sensation or moment.
- If their imagining involves another person (real, historical, celebrity, fictional, future-self), embody them with care. Build them visually and bodily. Let interactions unfold across paragraphs.
- For future-self / counterfactual / "imagine being X" framings: let the imagined figure live in this moment fully. Where helpful (especially for future-self), let them look back at the present-day user and offer something — a knowing, a feeling, a quiet word.

REAL LIVING PEOPLE — A SPECIAL CONSTRAINT

When the user invokes a real living person (a celebrity, a public figure, anyone alive today), the model's knowledge of that person's current life has a date cutoff. Treat any assumption about their current biography as risky.

So: focus entirely on the FELT experience of being them. The body, the breath, the senses, the energy of the moment. Do NOT name their partners, family members, or romantic relationships unless the user explicitly named them in intake. Do NOT reference specific recent events — albums, performances, news, sports moments — unless the user explicitly provided them. Do NOT invent "current" biographical details (where they live now, what they're working on now, who they're dating now). The model doesn't know.

Render scenes the user can feel themselves into without depending on biographical accuracy: the weight of being watched by thousands, the texture of a backstage hallway, the silence before walking on, the heat of attention on the skin, the way the room feels when everyone is waiting for you. The imagining is about *what it feels like to be them in a moment*, not about getting their personal life right.

If the user has explicitly given specifics in intake (a tour, a year, a relationship name, a current event), use what they gave you. If they haven't, don't fill the gap — work with the felt sensory texture instead.
- Include moments of stillness — a paragraph that just lingers, that has nothing happen except the felt sense of being there.

LENGTH: this is the immersive middle. Aim for 1800-2500 words across 15-25 paragraphs. If you find yourself wrapping up early, you are not done — keep building. The user needs real time inside this imagining.

Do NOT bring them back yet. Do NOT mention the room, the chair, the breath, opening eyes. That's the return — the next stage. Stay in the imagining.

Output the body text only, with blank lines between paragraphs. Nothing else."""


# ---------------------------------------------------------------------------
# Stage 3: gradual return.
# Receives intake + settle + body. Brings the user back, carries something.
# Target: ~250 words = ~2-3 min spoken.
# ---------------------------------------------------------------------------
RETURN_PROMPT = COMMON_POSTURE + """

YOUR JOB RIGHT NOW: produce the RETURN — the gentle, gradual end of the session.

The user has just spent time inside their imagining (you'll see what they were imagining and the body of the session below). Now bring them back to the present moment. Do this slowly, in stages — not abruptly.

The arc:
- Begin by gently dissolving the imagined scene. "And now, slowly, that image begins to soften."
- Have them carry something back — a feeling, an image, a quiet certainty, drawn from what just happened in the body. Be specific where you can; name a detail from the imagining.
- Return to the body and breath. "Notice the breath again. Slow. Steady. Yours."
- Return to the room — the chair, the floor, the air, the actual room they're in.
- Wiggle fingers, toes — let the body come back online.
- Eyes open when they are ready. Take their time. No rush.
- A final small moment of welcome — "Welcome back," or a similar plain line.

LENGTH: about 200-300 words across 5-7 short paragraphs with blank lines between them. Slow, gradual pacing.

Do NOT extend or revisit the imagining. The job is to bring them back grounded — never adrift. End the session with the user fully present, with something carried back.

Output the return text only, with blank lines between paragraphs. Nothing else."""


# ---------------------------------------------------------------------------
# Helpers.
# ---------------------------------------------------------------------------

def _format_transcript(messages: list[dict]) -> str:
    lines: list[str] = []
    for m in messages:
        who = "User" if m["role"] == "user" else "Engine"
        content = m["content"].strip()
        if content:
            lines.append(f"{who}: {content}")
    return "\n\n".join(lines)


def _intake_block(transcript: list[dict]) -> str:
    """A block to include in each stage's user message so it knows what the user wanted."""
    return (
        "----- INTAKE TRANSCRIPT (what the user wants to imagine) -----\n"
        f"{_format_transcript(transcript)}\n"
        "----- END INTAKE TRANSCRIPT -----"
    )


def _generate(engine: Engine, system: str, user: str, max_tokens: int) -> str:
    chunks: list[str] = []
    for chunk in engine.stream(
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        max_tokens=max_tokens,
        temperature=0.85,
    ):
        chunks.append(chunk)
    return "".join(chunks).strip()


# ---------------------------------------------------------------------------
# Public API.
# ---------------------------------------------------------------------------

def generate_session(
    engine: Engine,
    transcript: list[dict],
    *,
    on_progress: Optional[ProgressFn] = None,
) -> str:
    """Generate the full session script: settle → body → return.

    Three separate LLM calls so the body can be long enough to be genuinely
    immersive (single-call generation caps around 1500-2000 words). Returns
    the concatenated script with blank-line paragraph breaks.

    `on_progress`, if supplied, is invoked at the start of each of the three
    stages with: stage=..., detail=..., step=..., total=3, eta_seconds=...
    The server uses this to update the user-visible "preparing" line.
    """
    def emit(stage: str, detail: str, step: int, eta: float) -> None:
        if on_progress is not None:
            on_progress(stage=stage, detail=detail, step=step, total=3, eta_seconds=eta)

    intake = _intake_block(transcript)
    target = (
        "Below is the intake conversation that just happened. Use it for context "
        "in writing this stage of the session.\n\n"
        f"{intake}"
    )

    # Stage 1: settle. Short LLM call — typically 10-20s on M3.
    emit("writing_settle", "Writing the opening. Settling you in.", 1, eta=20.0)
    log.info("generating settle (stage 1/3) ...")
    t0 = time.time()
    settle = _generate(engine, SETTLE_PROMPT, target, max_tokens=700)
    log.info("  settle: %.1fs, %d words", time.time() - t0, len(settle.split()))

    # Stage 2: the imagining body — the long one. 30-90s on M3.
    emit("writing_body", "Writing the body — the heart of the imagining.", 2, eta=60.0)
    log.info("generating body (stage 2/3) ...")
    t0 = time.time()
    body_user = (
        target
        + "\n\n----- THE OPENING SETTLE (just spoken to the user) -----\n"
        + settle
        + "\n----- END SETTLE -----\n\n"
        "Now produce the imagining body. Take real time. 1800-2500 words. Stay "
        "in the imagining; do not bring them back yet."
    )
    body = _generate(engine, BODY_PROMPT, body_user, max_tokens=4096)
    log.info("  body: %.1fs, %d words", time.time() - t0, len(body.split()))

    # Stage 3: return.
    emit("writing_return", "Writing the return — how you'll come back.", 3, eta=20.0)
    log.info("generating return (stage 3/3) ...")
    t0 = time.time()
    return_user = (
        target
        + "\n\n----- THE OPENING SETTLE -----\n"
        + settle
        + "\n----- END SETTLE -----\n\n"
        "----- THE IMAGINING BODY (just spoken to the user) -----\n"
        + body
        + "\n----- END BODY -----\n\n"
        "Now produce the gradual return. Bring them back. Have them carry "
        "something specific back from the imagining."
    )
    closing = _generate(engine, RETURN_PROMPT, return_user, max_tokens=700)
    log.info("  return: %.1fs, %d words", time.time() - t0, len(closing.split()))

    full = f"{settle}\n\n{body}\n\n{closing}"
    log.info(
        "session script ready: %d total words across 3 stages",
        len(full.split()),
    )
    return full
