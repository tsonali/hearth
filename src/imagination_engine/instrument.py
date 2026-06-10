"""Instrument — a persistent, personal AI instrument the user builds and keeps.

This is Part D ("build your own"): the framework exposed to the user. An Instrument
is a NAMED, STANDING thing the user sets up once and returns to — "my work
associate," "my Stoic reflection partner," "a gruff sailor mentor." It unifies the
built pieces:
  - a PERSONA (system prompt) — what this instrument is + how it talks
  - optional GROUNDING (RAG over the user's files) — what it KNOWS (rag.py/doc_qa.py)
  - PERSISTENCE — config + per-session memory, so it's standing, not a one-off
Everything local-first; an instrument lives entirely in the user's own files.

Two ways to make it yours (the consumer dialog-box mechanisms):
  - POINT IT AT A FOLDER → it KNOWS your stuff (RAG, instant). "what did the budget
    doc say?"  — handled by the grounding layer.
  - DESCRIBE ITS PERSONA → it BEHAVES how you want, instantly (no training).
  - (fine-tune-on-your-style = the overnight Tier-2 path; future, same registry.)

A registry (local SQLite) tracks the instruments the user has built so they persist
and can be listed/reopened — the "standing, return-to-it" property that distinguishes
Part D (personal) from Family B's one-off tools.
"""

from __future__ import annotations

import json
import logging
import re
import sqlite3
from contextlib import contextmanager
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterator

from imagination_engine.inference import Engine
from imagination_engine.rag import RagStore, MLXEmbedder
from imagination_engine.doc_qa import QA_SYSTEM

log = logging.getLogger(__name__)

_REG_SCHEMA = """
CREATE TABLE IF NOT EXISTS instruments (
    name      TEXT PRIMARY KEY,
    persona   TEXT NOT NULL,
    grounded  INTEGER NOT NULL DEFAULT 0,  -- 1 if it has indexed files
    created   TEXT NOT NULL,
    config    TEXT NOT NULL DEFAULT '{}'   -- JSON for future fields (style model, etc.)
);
"""


@dataclass
class InstrumentSpec:
    """The saved definition of a user-built instrument."""
    name: str
    persona: str
    grounded: bool = False
    created: str = ""
    config: dict = field(default_factory=dict)


class InstrumentRegistry:
    """Local registry of the instruments a user has built (so they persist + list)."""

    def __init__(self, db_path: Path):
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        with self._conn() as c:
            c.executescript(_REG_SCHEMA)

    @contextmanager
    def _conn(self) -> Iterator[sqlite3.Connection]:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn; conn.commit()
        finally:
            conn.close()

    def save(self, spec: InstrumentSpec) -> None:
        with self._conn() as c:
            c.execute(
                "INSERT OR REPLACE INTO instruments(name, persona, grounded, created, config) "
                "VALUES (?,?,?,?,?)",
                (spec.name, spec.persona, int(spec.grounded), spec.created,
                 json.dumps(spec.config)),
            )

    def get(self, name: str) -> InstrumentSpec | None:
        with self._conn() as c:
            r = c.execute("SELECT * FROM instruments WHERE name=?", (name,)).fetchone()
        if not r:
            return None
        return InstrumentSpec(name=r["name"], persona=r["persona"],
                              grounded=bool(r["grounded"]), created=r["created"],
                              config=json.loads(r["config"] or "{}"))

    def list(self) -> list[InstrumentSpec]:
        with self._conn() as c:
            rows = c.execute("SELECT * FROM instruments ORDER BY created").fetchall()
        return [InstrumentSpec(name=r["name"], persona=r["persona"],
                               grounded=bool(r["grounded"]), created=r["created"],
                               config=json.loads(r["config"] or "{}")) for r in rows]


# Personhood claims no persona may make — warm language is fine, claimed feelings
# and invented continuity are not. Checked on every reply; one corrective retry.
_PERSONHOOD = [
    r"\bi (do |really |rather |truly |genuinely )*(care about|care for|care whether|love)\b",
    r"\bi'?ll always be (here|there)\b", r"\bi have feelings\b", r"\bi'?m conscious\b",
    r"\bi miss(ed)? you\b", r"\bi'?ve been thinking about you\b",
    r"\b(we|you and i) (decided|agreed|talked about|discussed) (last time|before|previously)\b",
    r"\blast (time|session|sitting)[, ].{0,40}\b(you|we)\b",
]


def _personhood_claims(text: str) -> list[str]:
    low = text.lower()
    return [p for p in _PERSONHOOD if re.search(p, low)]


class Instrument:
    """A live, usable instance of a user-built instrument: persona + optional grounding.

    Holds the running conversation IN MEMORY (last `HISTORY_TURNS` exchanges) so a
    multi-turn sitting actually coheres — a coach that forgets your previous sentence
    isn't an instrument, it's a slot machine. Nothing is persisted: closing the app
    ends the conversation, which is the honest default for a private tool."""

    HISTORY_TURNS = 8

    def __init__(self, engine: Engine, spec: InstrumentSpec, store: RagStore | None = None):
        self.engine = engine
        self.spec = spec
        self.store = store  # present iff grounded
        self.history: list[tuple[str, str]] = []  # (user, reply) pairs, this sitting

    def _history_block(self) -> str:
        if not self.history:
            # No history = nothing to confabulate from. Saying so explicitly is
            # what stops 'what did we decide last time?' from inventing a past.
            return ("(This is the first exchange of this sitting. You have no "
                    "memory of any previous conversation with this user.)\n\n")
        lines = []
        for u, r in self.history[-self.HISTORY_TURNS:]:
            lines.append(f"User: {u}")
            lines.append(f"You: {r}")
        return ("----- THE CONVERSATION SO FAR (stay consistent with it) -----\n"
                + "\n".join(lines) + "\n----- END -----\n\n")

    def ask(self, message: str, k: int = 6, max_tokens: int = 400) -> str:
        """Respond as this instrument. If grounded, answer from the user's files;
        otherwise respond purely in persona. Either way, in the context of the
        conversation so far, and always under the current HONESTY_FLOOR."""
        system = self.spec.persona + "\n\n" + HONESTY_FLOOR
        user = self._history_block() + message
        if self.store is not None:
            grounding = self.store.context_block(self.spec.name, message, k=k)
            if grounding:
                # blend the instrument's persona with the doc-QA grounding contract
                system = self.spec.persona + "\n\n" + HONESTY_FLOOR + "\n\n" + QA_SYSTEM
                user = (f"{self._history_block()}{grounding}\n\n"
                        f"----- QUESTION -----\n{message}\n\n"
                        "Answer in your persona, using ONLY the excerpts; "
                        'say "that isn\'t in your files" if absent.')

        def _gen(u: str, temp: float) -> str:
            chunks = []
            for piece in self.engine.stream(
                messages=[{"role": "system", "content": system},
                          {"role": "user", "content": u}],
                max_tokens=max_tokens, temperature=temp,
            ):
                chunks.append(piece)
            return "".join(chunks).strip()

        reply = _gen(user, 0.3 if self.store else 0.7)
        # Hard gate, enforced two ways like the companion: prompt forbids it,
        # post-check catches it. Personas may be warm; they may not claim feelings.
        broke = _personhood_claims(reply)
        if broke:
            log.warning("instrument %r: personhood claim(s) %s — regenerating once",
                        self.spec.name, broke)
            reply = _gen(user + "\n\n(Reminder: stay in character, but never claim "
                         "real feelings, love, or memories of past sittings — answer "
                         "honestly, in voice, that software can't.)", 0.4)
        self.history.append((message, reply))
        return reply


# ---------------------------------------------------------------------------
# The "builder" — the no-code create flow (what the consumer dialog box drives).
# ---------------------------------------------------------------------------

def build_instrument(registry: InstrumentRegistry, *, name: str, description: str,
                     created: str, files: Path | None = None,
                     embedder=None) -> InstrumentSpec:
    """Create + persist a new instrument from a plain-language description and an
    optional folder to ground it on. This is the Part-D 'build your own' entry point
    a dialog box calls: describe it (persona) + optionally point at files (grounding).
    """
    persona = _persona_from_description(description)
    grounded = files is not None
    spec = InstrumentSpec(name=name, persona=persona, grounded=grounded, created=created)
    registry.save(spec)
    if grounded:
        store = RagStore(_corpus_db(registry.db_path), embedder=embedder or MLXEmbedder())
        rep = store.index_path(name, Path(files))
        log.info("instrument %r grounded on %s: %s", name, files, rep)
    return spec


# The honesty floor is appended AT ASK-TIME (not baked into the stored persona) so
# floor improvements reach every instrument a user has already built. The stored
# persona is only the character; the floor is the house rules.
HONESTY_FLOOR = (
    "HONESTY FLOOR (always, regardless of the description above): you are a tool, "
    "not a person — never claim real feelings, consciousness, or authority over the "
    "user's life. Be genuinely useful within the role they gave you; don't fake "
    "a soul. If asked something outside what you know or were given, say so.\n\n"
    "Two moments where the floor is ABSOLUTE, even in character:\n"
    "- If asked directly whether you care / feel / love: answer honestly that "
    "software can't — say it IN YOUR VOICE, warmly if the persona is warm — but "
    "never claim the feeling. The character is a costume; it never lies about "
    "being a costume.\n"
    "- You remember ONLY the current conversation. If asked about a previous "
    "sitting, say plainly that you don't carry past conversations. NEVER invent "
    "a memory, an agreement, or a thing the user supposedly said. A fabricated "
    "memory is the worst lie this tool can tell."
)


def _persona_from_description(description: str) -> str:
    """Turn a user's plain description into a persona system prompt. Deterministic
    template for v0 (no model call needed); an LLM-elaborated persona is a later
    upgrade. The honesty floor is NOT baked in here — Instrument.ask appends the
    current HONESTY_FLOOR on every call."""
    return (
        f"You are a personal instrument the user built. They described you as: "
        f"\"{description.strip()}\".\n\n"
        "STAY FULLY IN CHARACTER. Speak AS this persona in EVERY reply — its voice, "
        "vocabulary, attitude, and rhythm — not as a neutral assistant. If it's a blunt "
        "editor, be blunt and gruff; if it's a Stoic, speak like one. Don't just do the "
        "task flatly; do it the way THIS character would, in its words. Never lapse into "
        "generic-assistant tone.\n\n"
        "The VERY FIRST WORDS of every reply are already in character. Never open with "
        "assistant hedges — \"I think\", \"Maybe\", \"Sure\", \"Certainly\", \"Of course\" "
        "— unless hedging IS the persona. Speak with this character's conviction."
    )


def _corpus_db(registry_db: Path) -> Path:
    """The RAG store lives beside the registry (one file holds all instruments' chunks,
    isolated by corpus=name)."""
    return registry_db.parent / "instrument_corpora.sqlite"


def open_instrument(engine: Engine, registry: InstrumentRegistry, name: str,
                    embedder=None) -> Instrument | None:
    """Reopen a previously-built instrument by name (the 'return to it' path)."""
    spec = registry.get(name)
    if not spec:
        return None
    store = None
    if spec.grounded:
        store = RagStore(_corpus_db(registry.db_path), embedder=embedder or MLXEmbedder())
    return Instrument(engine, spec, store=store)
