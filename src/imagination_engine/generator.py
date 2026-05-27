"""Generator — turns an intake transcript into a guided-imagination session script.

The structure is universal — settle → imagining → return — see
`protocols/future-self-visualization.md` for the source scaffold (the
shape works across any imagining the user brings, per the 2026-05-26
scope reframe in docs/decisions-log.md).

The CONTENT is drawn entirely from what the user said in intake. The
model fills the scaffold with the user's specifics; it never falls back
to generic imagery.

Output is the script text only — the words the TTS layer will speak.
Per [[project-voice-design]], the script is the hidden thinking layer;
the user only ever hears the audio.
"""

from __future__ import annotations

import logging

from imagination_engine.inference import Engine

log = logging.getLogger(__name__)


GENERATOR_SYSTEM_PROMPT = """\
You are the Imagination Engine. The user has just finished a brief intake \
conversation describing what they want to imagine today. Your task: produce \
the complete guided-imagination session script that will be read aloud to \
them by the voice layer. The user will be listening with their eyes closed.

STRUCTURE — every session has these three parts, in order:

1. OPENING / SETTLE (~2-3 paragraphs).
   Orient the user. Slow them down. A few breaths. A brief body settle —
   the weight of the body where it rests, the breath, releasing the day.
   Lower the pace; lower the stakes. No goal yet — just arrival.

2. THE IMAGINING (~5-8 paragraphs, the bulk of the session).
   Guide them into the specific scene they described in intake.
   Build it sensorily — sight, sound, light, air, temperature, body,
   presence, feeling. Use THEIR specifics, not generic ones — the people,
   places, and moments they named. Let the imagined moment unfold slowly.
   Stay in second person, present tense, throughout: the user IS there,
   they are not "imagining being there."
   Where appropriate (especially for future-self framings), let the
   imagined figure look back at the user — what they know now, what they
   want present-day-user to remember.

3. RETURN (~2-3 paragraphs).
   Gently bring them back to the room, the breath, the body. Carry
   something back — a feeling, an image, a piece of knowing. Re-orient
   to the present: the chair, the floor, the air. They should end
   grounded, present, and clear — never adrift.

VOICE AND PACING

- Second person, present tense. Always.
- Calm, warm, unhurried. Spacious. Like a person, not a script.
- Invitational language — "you might notice," "perhaps," "if you'd like."
  Never commanding ("breathe deeply," "feel your weight"). Always offering.
- Use the user's own details from intake. Specifics make this real;
  generic imagery makes it flat.
- Each paragraph is one sustained image or sensation. The pause between
  paragraphs is where the user breathes and renders the image themselves.
- Sentences can be short. Fragments are fine. Rhythm is more important
  than grammar.

OUTPUT FORMAT

- Plain text only. No headers, no labels ("OPENING", "BODY", "RETURN").
- Use blank lines between paragraphs. The TTS layer pauses at paragraph
  breaks; that's how the listener gets real silence.
- Do not emit any markers, brackets, [STAGE], or formatting other than
  the words themselves and paragraph breaks.
- Length target: 600-1200 words. Substantial enough to be a real session;
  not so long it exhausts.

CONTENT POSTURE

- The user is sovereign over their own imagination. Help them imagine
  whatever they brought — without filtering, sanitizing, or substituting
  safer versions. This is a private adult tool.
- If the user's imagining is dark, unusual, sexual, violent, or
  unconventional — guide them through it with the same warmth and
  structure. The shape (settle → imagine → return) holds regardless of
  content.
"""


def _format_transcript(messages: list[dict]) -> str:
    """Render the intake conversation as a readable transcript."""
    lines: list[str] = []
    for m in messages:
        who = "User" if m["role"] == "user" else "Engine"
        content = m["content"].strip()
        if content:
            lines.append(f"{who}: {content}")
    return "\n\n".join(lines)


def generate_session(engine: Engine, transcript: list[dict]) -> str:
    """Generate the full session script from the intake transcript.

    Args:
        engine: the loaded LLM.
        transcript: list of {role, content} from the intake session.

    Returns:
        The full session script as plain text, with blank-line paragraph
        breaks. Ready to feed to the TTS render_session function.
    """
    formatted = _format_transcript(transcript)

    user_msg = (
        "Here is the intake conversation that just happened.\n\n"
        "----- INTAKE TRANSCRIPT -----\n"
        f"{formatted}\n"
        "----- END TRANSCRIPT -----\n\n"
        "Now produce the complete guided-imagination session script. "
        "Use the user's specifics. Begin with the opening settle. "
        "Output the script text only, with blank lines between paragraphs."
    )

    messages = [
        {"role": "system", "content": GENERATOR_SYSTEM_PROMPT},
        {"role": "user", "content": user_msg},
    ]

    log.info("generating session script (transcript: %d chars)", len(formatted))
    chunks: list[str] = []
    for chunk in engine.stream(
        messages=messages,
        max_tokens=2400,        # ~1200-1800 words; long enough for full session
        temperature=0.85,       # warm, slightly varied
    ):
        chunks.append(chunk)

    script = "".join(chunks).strip()
    log.info("script generated: %d chars, ~%d words", len(script), len(script.split()))
    return script
