"""Intake comprehension — resolve the user's prompt into a structured field.

Separates comprehension from generation, per the v4-postmortem critique:
trying to pattern-match the user's phrasing inside the generation prompt
(the v4 CASE A / CASE B rule) is brittle and misses the next phrasing.
Better architecture: one cheap LLM call after intake produces a structured
`Classification` that the generator consumes — no more prompt-time
intent parsing.

The Classification answers three questions the generator otherwise has
to guess:

  1. Embodiment direction. Is the listener IS the subject (CASE A:
     "imagine me as Taylor Swift" — you ARE Taylor) or are they
     themselves with a subject present (CASE B: "imagine Harry Styles
     is in love with me" — you are yourself, Harry is there) or is
     there no named subject at all (CASE C: "imagine being on a quiet
     mountain" — listener in a scene, no other character)?

  2. The subject's name and what they are. The string the body prompt
     anchors on. "Taylor Swift" is more useful than "celebrity"; "a
     calmer braver version of yourself" is more useful than "different
     personality."

  3. Concrete sensory anchors. 3-5 specific objects / textures /
     positions the body should hit. The user gave these in intake;
     surfacing them as a structured list keeps the generator from
     dropping them.
"""

from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass, field
from typing import Literal

from imagination_engine.inference import Engine

log = logging.getLogger(__name__)


Direction = Literal["case_a", "case_b", "case_c"]


@dataclass
class Classification:
    """Structured comprehension of a user's intake transcript.

    Produced by `classify_intake`, consumed by the generator. Round-trips
    cleanly through to_dict / from_dict so it can be cached on the
    IntakeSession.
    """

    direction: Direction = "case_c"
    subject: str = ""               # the named entity, if any
    subject_kind: str = ""          # "real_living_person" | "fictional" | "self_variant" | "abstract" | ""
    scene_summary: str = ""         # one sentence: where/what the scene is
    anchors: list[str] = field(default_factory=list)  # 3-5 concrete sensory anchors
    raw: str = ""                   # the raw model output, kept for debugging

    def to_dict(self) -> dict:
        return {
            "direction": self.direction,
            "subject": self.subject,
            "subject_kind": self.subject_kind,
            "scene_summary": self.scene_summary,
            "anchors": list(self.anchors),
        }

    @classmethod
    def from_dict(cls, d: dict) -> "Classification":
        return cls(
            direction=d.get("direction", "case_c"),
            subject=d.get("subject", ""),
            subject_kind=d.get("subject_kind", ""),
            scene_summary=d.get("scene_summary", ""),
            anchors=list(d.get("anchors", [])),
        )

    def direction_block(self) -> str:
        """A short prose block describing the embodiment direction.

        Injected into the body / beat-generator prompts so they don't have
        to interpret the intake themselves.
        """
        if self.direction == "case_a":
            who = self.subject or "the subject the user named"
            return (
                f"EMBODIMENT: CASE A. The listener IS {who}. "
                f"Write the script from inside {who}'s body. "
                f"'You' refers to {who} throughout. "
                f"Describe {who}'s posture, breath, hands, sensory experience."
            )
        if self.direction == "case_b":
            who = self.subject or "the subject the user named"
            return (
                f"EMBODIMENT: CASE B. The listener is themselves. "
                f"{who} is present in the scene with them. "
                f"'You' refers to the listener throughout. "
                f"Describe {who}'s presence — their voice, manner, hands, "
                f"behavior — but the script is anchored in the listener's own body."
            )
        return (
            "EMBODIMENT: CASE C. The listener is themselves in a scene with "
            "no other specific character. 'You' refers to the listener throughout. "
            "Build the scene around them."
        )


CLASSIFIER_SYSTEM_PROMPT = """\
You read an intake transcript and produce a structured comprehension of \
what the user wants to imagine. Output STRICT JSON only — no prose, no \
commentary, no markdown fences. The JSON has exactly these keys:

{
  "direction": "case_a" | "case_b" | "case_c",
  "subject": "<the named entity, or empty string>",
  "subject_kind": "real_living_person" | "fictional" | "self_variant" | "abstract" | "",
  "scene_summary": "<one sentence describing where and what the scene is>",
  "anchors": ["<concrete sensory anchor 1>", "<2>", "<3>", ...]
}

RULES FOR DIRECTION (this is the most important field):

CASE A — Listener IS the subject. The script is written from INSIDE the subject's body.
Triggers (user phrasings):
  - "imagine me AS [X]" → case_a, subject=[X]
  - "imagine being [X]" → case_a, subject=[X]
  - "imagine me WITH [a capability/state]" → case_a, subject="self with [capability]"
  - "imagine me [achieving something]" → case_a, subject="self [achievement]"
  - "imagine a different version of me" → case_a, subject="alternate self"

CASE B — Listener is themselves; subject is PRESENT in the scene.
Triggers:
  - "imagine [X] is in love with me" → case_b, subject=[X]
  - "imagine being with [X]" → case_b, subject=[X]
  - "imagine [X] tells me / does something to me / loves me" → case_b, subject=[X]
  - "imagine my [parent/partner/friend] [verb]ing me" → case_b, subject="the named person"

CASE C — No specific other character; listener is themselves in a scene.
Triggers:
  - "imagine being on a quiet mountain" → case_c
  - "imagine a perfect Tuesday morning" → case_c
  - "imagine I lived in Paris" → case_c, subject="Paris" (the place is the focus)

If ambiguous between A and B, default to A. If no named subject at all, use C.

SUBJECT_KIND:
  - "real_living_person" — a celebrity, public figure, anyone alive today (Taylor Swift, Harry Styles, etc.)
  - "fictional" — a character from a book/film/show (Hermione, Sherlock, etc.)
  - "self_variant" — a version of the user themselves (future self, braver self, etc.)
  - "abstract" — a role/state with no specific identity (a billionaire, an Olympic athlete, a person with photographic memory)
  - "" — no subject (CASE C with just a scene/place)

ANCHORS: pull 3-5 concrete sensory anchors from the user's intake (BOTH the user's messages AND the engine's clarifying questions, since the user may have agreed implicitly with the engine's framing). Anchors are SHORT noun phrases naming specific things: "stage floor", "mic in right hand", "warmth across sternum", "the smell of hairspray", "the cold concrete backstage hallway", "her shoulders wider than mine". They are the textures the body of the script should hit. If the intake is thin, pull what's there; do not invent.

SCENE_SUMMARY: one sentence, declarative. Examples:
  - "On stage as Taylor Swift, the moment just before stepping out for a sold-out show."
  - "In a private room with Harry Styles, intimate quiet evening, his attention on you."
  - "A retired-young Tuesday morning with no obligation, in a comfortable home."

Output ONLY the JSON. Do not wrap in code fences. Do not add commentary."""


def _format_transcript(messages: list[dict]) -> str:
    lines = []
    for m in messages:
        who = "User" if m["role"] == "user" else "Engine"
        content = m["content"].strip()
        if content:
            lines.append(f"{who}: {content}")
    return "\n\n".join(lines)


def _extract_json(text: str) -> dict:
    """Pull the first JSON object out of the model's response.

    Models trained on RLHF sometimes wrap JSON in ```json``` fences or
    prepend a sentence. Be tolerant of both.
    """
    # Strip code fences if present
    text = re.sub(r"^```(?:json)?\s*", "", text.strip())
    text = re.sub(r"\s*```$", "", text)

    # Find the outermost JSON object
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end < start:
        raise ValueError(f"no JSON object found in: {text!r}")
    candidate = text[start:end + 1]
    return json.loads(candidate)


def classify_intake(engine: Engine, transcript: list[dict]) -> Classification:
    """Classify a completed intake transcript.

    One LLM call. Returns a Classification. If JSON parsing fails (model
    misbehaved), returns a CASE C default with the raw text saved for
    debugging — the generator falls through to its no-classification
    behavior.
    """
    user_msg = (
        "Here is the intake transcript. Produce the JSON classification.\n\n"
        "----- INTAKE TRANSCRIPT -----\n"
        + _format_transcript(transcript)
        + "\n----- END TRANSCRIPT -----"
    )

    chunks: list[str] = []
    for chunk in engine.stream(
        messages=[
            {"role": "system", "content": CLASSIFIER_SYSTEM_PROMPT},
            {"role": "user", "content": user_msg},
        ],
        max_tokens=400,
        temperature=0.3,  # low temperature — we want consistent JSON
    ):
        chunks.append(chunk)
    raw = "".join(chunks).strip()

    try:
        data = _extract_json(raw)
        cls = Classification.from_dict(data)
        cls.raw = raw
        log.info("intake classified: direction=%s, subject=%r, anchors=%d",
                 cls.direction, cls.subject, len(cls.anchors))
        return cls
    except (ValueError, json.JSONDecodeError) as e:
        log.warning("intake classification failed (%s); falling back to CASE C. raw=%r",
                    e, raw[:200])
        return Classification(raw=raw)
