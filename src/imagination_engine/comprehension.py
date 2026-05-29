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
from imagination_engine.structured import extract_object

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
    archetype: str = ""             # matched scene-bible archetype, or "" if none fits
    raw: str = ""                   # the raw model output, kept for debugging

    def to_dict(self) -> dict:
        return {
            "direction": self.direction,
            "subject": self.subject,
            "subject_kind": self.subject_kind,
            "scene_summary": self.scene_summary,
            "anchors": list(self.anchors),
            "archetype": self.archetype,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "Classification":
        return cls(
            direction=d.get("direction", "case_c"),
            subject=d.get("subject", ""),
            subject_kind=d.get("subject_kind", ""),
            scene_summary=d.get("scene_summary", ""),
            anchors=list(d.get("anchors", [])),
            archetype=(d.get("archetype") or "").strip(),
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
  "scene_summary": "<2-3 sentences describing the specific scene>",
  "anchors": ["<concrete sensory anchor 1>", "<2>", "<3>", "<4>", "<5>", "<6>", "<7>"]
}

══════════════════════════════════════════════════════════
THE MOST IMPORTANT INSTRUCTION:
══════════════════════════════════════════════════════════

The user's intake is usually SPARSE. They will say something like \
"imagine me as Taylor Swift" or "imagine me retiring young" or \
"imagine me with a different personality" and then "just start now" \
WITHOUT giving you details about where, when, who, or what.

DO NOT treat sparseness as a reason to give back generic content. \
IMPROVISE BOLDLY. Commit to specific concrete details that fit the \
asked-for scenario — a specific time, place, outfit, situation, \
moment, mood. The downstream beat planner needs RICH SPECIFIC CANVAS \
to work from. Generic "stage / spotlight / crowd" anchors produce \
generic scripts. "The silver bodysuit / the in-ear monitor pressed \
against your temple / the tunnel-roar of forty thousand voices through \
the corridor wall" produce immersive scripts.

A great writer given a five-word prompt does not ask for more. They \
commit to a specific imagined scene and trust their reader to be \
drawn into it. You are that writer.

GOOD vs BAD examples for SCENE_SUMMARY and ANCHORS given thin intake:

User: "imagine me as Taylor Swift"
BAD (what the previous version of this prompt produced):
  scene_summary: "On stage, spotlight shining with Taylor Swift as you."
  anchors: ["spotlight", "stage"]
GOOD:
  scene_summary: "Backstage in a stadium tunnel, three minutes before
    you step out for tonight's Eras Tour show. The silver bodysuit. The
    in-ear cuing you in. Your stylist just touched up your lip."
  anchors: ["silver bodysuit against your skin", "the in-ear monitor
    pressure on your right temple", "the tunnel-roar of forty thousand
    voices through the corridor wall", "the cold concrete under your
    boot heels", "the taste of metal in the back of your mouth",
    "your stylist's hand on the small of your back", "the click of
    the audio tech's voice in your ear"]

User: "imagine me retiring young and wealthy"
BAD:
  scene_summary: "A retired-young Tuesday morning with no obligation."
  anchors: ["beach", "sunset"]
GOOD:
  scene_summary: "A weekday morning at your house on the Pacific coast.
    You just got off a call with your architect about the new wing.
    The light is everywhere and there's nothing on your calendar."
  anchors: ["the long pause in your day with nothing waiting on it",
    "the smell of espresso the housekeeper made an hour ago", "the
    weight of a phone that doesn't need answering", "your bare feet
    on cool kitchen tile", "the sound of a single distant lawnmower",
    "the worn-in cushion of a chair you bought for yourself", "an
    almond croissant cooling on a plate you don't have to wash"]

User: "imagine me with a different personality"
BAD:
  scene_summary: "In an environment where the new personality thrives."
  anchors: ["environment", "thrive"]
GOOD:
  scene_summary: "You are the version of you who takes a beat before
    answering, who lets pauses sit. You're at a party in your own
    apartment, mid-conversation with someone, and you have all the
    time in the world."
  anchors: ["the lower place your breath sits in your chest", "the
    wider stance through your hips", "the half-smile you let stay
    on your face", "the cool of a glass against your palm", "the
    way you wait a full beat before speaking", "the room watching
    you, not the other way around", "your jaw unclenched"]

THE PATTERN: take the user's seed, IMPROVISE a specific scene with a
specific time, place, situation, mood, and 5-7 body-and-object-
specific anchors. Be specific even (especially) when the user wasn't.

CRITICAL — INVENT FRESH SPECIFICS:
The examples above show the SHAPE of good output, not the CONTENT to
copy. When the user's intake actually arrives, generate FRESH specifics
that fit THAT user's seed — do not reuse the example phrases. If the
user asks for Taylor Swift, do not mention silver bodysuits and Eras
Tour unless that genuinely fits; pick a different specific Taylor
moment. If the user asks for retiring young, do not mention Pacific
coast and almond croissants; pick a different specific retired-young
morning. The examples were illustrative — your output is yours.

══════════════════════════════════════════════════════════

RULES FOR DIRECTION (CASE A / CASE B / CASE C):

CASE A — Listener IS the subject. Triggers (user phrasings):
  - "imagine me AS [X]" → case_a, subject=[X]
  - "imagine being [X]" → case_a, subject=[X]
  - "imagine me WITH [a capability/state]" → case_a, subject="self with [capability]"
  - "imagine me [achieving something]" → case_a, subject="self [achievement]"

CASE B — Listener is themselves; subject is PRESENT.
Triggers:
  - "imagine [X] is in love with me" → case_b, subject=[X]
  - "imagine being with [X]" → case_b, subject=[X]
  - "imagine [X] tells me / does something to me" → case_b, subject=[X]

CASE C — No specific other character.
Triggers:
  - "imagine being on a quiet mountain" → case_c
  - "imagine a perfect Tuesday morning" → case_c

Default if ambiguous: case_a.

SUBJECT_KIND:
  - "real_living_person" — a celebrity, public figure, anyone alive today
  - "fictional" — a character from a book/film/show
  - "self_variant" — a version of the user themselves
  - "abstract" — a role/state with no specific identity (billionaire, Olympic athlete)
  - "" — no subject (CASE C with just a scene/place)

Output ONLY the JSON. Do not wrap in code fences. Do not add commentary."""


def _format_transcript(messages: list[dict]) -> str:
    lines = []
    for m in messages:
        who = "User" if m["role"] == "user" else "Engine"
        content = m["content"].strip()
        if content:
            lines.append(f"{who}: {content}")
    return "\n\n".join(lines)


# JSON extraction now lives in the framework-general `structured` module
# (handles fences, prose, trailing commas, control chars, and truncation
# salvage — far beyond the fence-only tolerance this used to have).


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

    # Inject the available scene-bible archetypes so the classifier maps the
    # intake to one — matching is the classifier's job (see scene_bibles README).
    # The generator binds the matched bible; "" means none fit -> improvise path.
    from imagination_engine import scene_bibles as _sb
    archetypes = _sb.archetype_names()
    system_prompt = CLASSIFIER_SYSTEM_PROMPT
    if archetypes:
        system_prompt += (
            "\n\n══════════════════════════════════════════════════════════\n"
            'ARCHETYPE — add one more JSON key, "archetype": pick the ONE '
            'best-fit archetype from this list, or "" if none genuinely fits '
            "(do NOT force a bad match):\n"
            + "\n".join(f"  - {a}" for a in archetypes)
        )

    chunks: list[str] = []
    for chunk in engine.stream(
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_msg},
        ],
        max_tokens=400,
        temperature=0.3,  # low temperature — we want consistent JSON
    ):
        chunks.append(chunk)
    raw = "".join(chunks).strip()

    try:
        data = extract_object(raw)
        cls = Classification.from_dict(data)
        cls.raw = raw
        if cls.archetype and cls.archetype not in archetypes:
            log.warning("classifier returned unknown archetype %r; ignoring", cls.archetype)
            cls.archetype = ""
        log.info("intake classified: direction=%s, subject=%r, anchors=%d, archetype=%r",
                 cls.direction, cls.subject, len(cls.anchors), cls.archetype)
        return cls
    except (ValueError, json.JSONDecodeError) as e:
        log.warning("intake classification failed (%s); falling back to CASE C. raw=%r",
                    e, raw[:200])
        return Classification(raw=raw)
