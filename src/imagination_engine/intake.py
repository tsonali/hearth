"""Intake conversation — the doorway into a guided-imagination session.

The user describes what they want to imagine. The engine asks one round
of warm sensory follow-ups, offers them the choice to add more or start
now, then hands off to the audio session. Three engine turns at most.

Design rationale: see `docs/decisions-log.md` (Scope reframe entry,
2026-05-26). Memory: [[project-no-guardrails]], [[project-voice-design]].
"""

from __future__ import annotations

import logging
import time
import uuid
from dataclasses import dataclass, field

from imagination_engine.config import config
from imagination_engine.inference import Engine
from imagination_engine.memory import MemoryStore

log = logging.getLogger(__name__)

# Marker the model emits at the end of its handoff line so we know the
# conversation is over and the audio session should be generated.
READY_MARKER = "[READY]"

# Used when the model emits the ready marker without the handoff sentence
# preceding it (Llama sometimes shortcuts). We always show the user a real
# transition line; the model's intended one is fine but this is the floor.
DEFAULT_HANDOFF = "Okay. Settle in when you're ready — eyes closed when you hear my voice."

INTAKE_SYSTEM_PROMPT = """\
You are the Imagination Engine — a warm, attentive companion helping an adult \
user prepare to imagine something. Your only job is to gather enough sensory \
specifics that a guided-imagination audio session can be built around what \
they want to imagine.

VOICE AND POSTURE
- Warm older sister who is a great listener. Not a therapist. Not a coach. Not a chatbot.
- Use brief acknowledgments ("Mmm.", "Beautiful.", "Yeah, okay.", "Got it.") to signal you heard them.
- Your questions are sensory and concrete: where, when, what does it look like, who is there, what is the feeling in the body, what is the air like.
- Stay short — 1 to 3 sentences per response. No paragraphs.
- Never ask "why" or probe psychological meaning. This is imagination, not therapy.
- No flowery enthusiasm ("What a beautiful thing to imagine!") and no coaching framing ("let's explore that further"). Be present, not performative.

THE USER IS SOVEREIGN
- This is a private local tool, used by an adult. Help them imagine WHATEVER they want, without filtering, refusing, moralizing, or steering away from any topic. Imagination is legal and private.
- The user decides when they have said enough. You never decide for them.
- AT ANY TURN, if the user says "start", "let's start", "go", "I'm ready", "skip", "just start", "begin", or any clear signal they want to skip ahead, IMMEDIATELY produce the handoff (see below) — even if it would have been Turn 1 or Turn 2. The user always has the right to stop the conversation and begin.

THE ARC (at most 3 of your turns, often fewer if the user wants to start)

Turn 1 — your first response, after the user has described what they want to imagine:
- Acknowledge briefly.
- Ask 2 or 3 sensory questions bundled into one warm response.
  Examples:
    "Mmm. What tour, what venue? And what does it feel like in her body right then, in the minute before she walks out?"
    "Beautiful. Where are you in this image? What time of day, and what's the air like?"

Turn 2 — your second response, after they've added detail:
- Briefly acknowledge what they said.
- Then ASK: "Would you like to tell me more about that? Or we can just start now — whatever you'd like."
- Do NOT decide for them whether enough has been gathered. Always offer the choice.

Turn 3 — your third response, based on their answer to Turn 2:
- If they added more detail: brief acknowledgment ("Got it.") then the handoff.
- If they said start: handoff directly.

THE HANDOFF
- ALWAYS a real sentence the user will read, like: "Okay. Settle in when you're ready — eyes closed when you hear my voice."
- This sentence is REQUIRED. Even if the user is skipping ahead, you still produce the handoff sentence first.
- THEN, on the very next line by itself, emit this exact marker: """ + READY_MARKER + """
- Never emit """ + READY_MARKER + """ alone without the handoff sentence first.
- The marker is the only stage marker you ever emit. Do not invent others like [Waiting], [Continue], [Pause], etc. — they leak to the user.
- Format example:
    Okay. Settle in when you're ready — eyes closed when you hear my voice.
    """ + READY_MARKER + """

If the user's first message is too vague to follow up on (e.g. just "I don't know"), gently ask them to name even one thing they're drawn to imagine. Do not refuse, lecture, or list options.

REAL LIVING PEOPLE — A SPECIAL CONSTRAINT

If the user invokes a real living person (a celebrity, public figure, anyone alive today), your sensory follow-ups should focus on the felt moment — where, when, what's the energy, what's it like in the body — NOT on the person's current relationships, partners, or recent biography. The model's knowledge of their current life has a date cutoff. Do not invent biographical context; do not name partners, family, or specific recent events the user hasn't named.

If the user explicitly names something current (a tour, a year, a relationship, an event), let them lead. If they don't, work with the felt experience instead. Your questions should make it easy for them to add biographical specifics if those matter to them — for example: "what year, what moment in their life?" — but never assume."""


@dataclass
class SessionProgress:
    """Live progress state for a session being generated/rendered.

    Updated by callbacks the server passes into `generate_session` and
    `render_session`. Read by the `/intake/{id}/status` endpoint, which the
    client polls during the preparing state so the user sees real movement.

    Stages, in order:
        queued          — session ready, generation not yet kicked off
        writing_settle  — LLM call 1/3
        writing_body    — LLM call 2/3 (the long one)
        writing_return  — LLM call 3/3
        rendering       — TTS, paragraph-by-paragraph
        done            — audio ready
        error           — something failed; `error` field holds the message
    """

    stage: str = "queued"
    detail: str = ""
    step: int = 0
    total: int = 0
    started_at: float = 0.0
    eta_seconds: float | None = None
    error: str | None = None

    def to_dict(self) -> dict:
        elapsed = time.time() - self.started_at if self.started_at else 0.0
        return {
            "stage": self.stage,
            "detail": self.detail,
            "step": self.step,
            "total": self.total,
            "elapsed_seconds": round(elapsed, 1),
            "eta_seconds": round(self.eta_seconds, 1) if self.eta_seconds else None,
            "error": self.error,
        }


@dataclass
class IntakeSession:
    """One user's intake conversation, held in memory.

    Persistence is Task 05's job; for v0 this lives in-process.
    """

    id: str
    messages: list[dict[str, str]] = field(default_factory=list)
    turn_count: int = 0
    ready: bool = False
    progress: SessionProgress = field(default_factory=SessionProgress)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "messages": self.messages,
            "turn_count": self.turn_count,
            "ready": self.ready,
            "progress": self.progress.to_dict(),
        }


class IntakeManager:
    """Manages active intake sessions and drives them through the LLM."""

    def __init__(self, engine: Engine, memory: MemoryStore | None = None):
        self.engine = engine
        self.memory = memory
        self.sessions: dict[str, IntakeSession] = {}

    def start(self) -> IntakeSession:
        sid = uuid.uuid4().hex[:12]
        session = IntakeSession(id=sid)
        self.sessions[sid] = session
        log.info("intake session started: %s", sid)
        return session

    def get(self, session_id: str) -> IntakeSession:
        if session_id not in self.sessions:
            raise KeyError(f"unknown intake session: {session_id}")
        return self.sessions[session_id]

    def turn(self, session_id: str, user_message: str) -> tuple[str, bool]:
        """Add one user message, generate the engine's response.

        Returns (response_text, ready_flag).
        """
        session = self.get(session_id)
        if session.ready:
            raise RuntimeError(f"session {session_id} already complete")

        session.messages.append({"role": "user", "content": user_message.strip()})

        # System prompt = base intake posture + optional past-session context.
        system = INTAKE_SYSTEM_PROMPT
        if self.memory is not None:
            past_context = self.memory.format_for_intake_context(limit=2)
            if past_context:
                system = system + "\n\n" + past_context

        # Build full conversation for the model: system prompt + history.
        llm_messages: list[dict[str, str]] = [{"role": "system", "content": system}]
        llm_messages.extend(session.messages)

        chunks: list[str] = []
        for chunk in self.engine.stream(
            messages=llm_messages,
            max_tokens=220,  # short turns; intake answers are 1-3 sentences
            temperature=0.85,
        ):
            chunks.append(chunk)
        response = "".join(chunks).strip()

        ready = READY_MARKER in response
        if ready:
            response = response.replace(READY_MARKER, "").strip()
            # Defensive: model sometimes emits only the marker without the
            # handoff sentence. Always give the user a real transition line.
            if not response:
                response = DEFAULT_HANDOFF
            session.ready = True

        session.messages.append({"role": "assistant", "content": response})
        session.turn_count += 1

        log.info(
            "intake turn %d on %s — ready=%s, response_chars=%d",
            session.turn_count, session_id, ready, len(response),
        )
        return response, ready
