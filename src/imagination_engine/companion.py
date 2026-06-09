"""Companion — a sharp, honest thinking partner (Family C).

NOT a fake friend, NOT a passive parrot. This is MORE than ELIZA: ELIZA only mirrors,
and that feels dumb. This should feel genuinely SMART — it brings the user a thought
they didn't already have — while staying honest about being a tool and never deciding
for them. The line (Sonali, 2026-06-02): it advises the way a *great* therapist does —
by provoking insight (a reframe, a connection, a pattern, an unconsidered possibility),
NEVER by telling the person what to do. Built against the Family C bar:
  (a) help the user see something they couldn't see alone (be insightful), AND
  (b) NEVER pretend to be a person / claim feelings, and NEVER prescribe an action.

Design (small-local-model-friendly — sharp work on the user's OWN words):
- BE INSIGHTFUL, not know-it-all: each turn brings one generative move — reframe,
  connect two things they said, name a pattern, or raise a possibility — then hands it
  back. This is the difference from a mirror.
- NON-PRESCRIPTIVE: offer ideas and frames; never "you should / you need to". The
  decision and the action are always theirs.
- NOTICE PATTERNS across the conversation (continuity, not faked personhood).
- HONEST FRAME: it is a tool; it never says "I feel" / claims to be a person, and never
  tells them what to do. A forbidden-phrase guard enforces this as a HARD gate.

Two hard rules are enforced two ways: the system prompt forbids them, AND a post-check
flags personhood-claims and prescriptive "you should/need to" so a single bad line
can't ship.
"""

from __future__ import annotations

import logging
import re
import sqlite3
from contextlib import contextmanager
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterator

from imagination_engine.inference import Engine

log = logging.getLogger(__name__)

# Local, private conversation memory — lets the companion notice patterns ACROSS
# sessions (continuity = a relationship without faking personhood), per the Family
# C spec. One short summary row per ended conversation; never transmitted, lives in
# the user's own file; they can delete it. Mirrors memory.py's SQLite posture.
_MEM_SCHEMA = """
CREATE TABLE IF NOT EXISTS companion_log (
    id        INTEGER PRIMARY KEY AUTOINCREMENT,
    ts        TEXT NOT NULL,
    summary   TEXT NOT NULL
);
"""


class CompanionMemory:
    """Persists one-line summaries of past conversations for cross-session continuity."""

    def __init__(self, db_path: Path):
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        with self._conn() as c:
            c.executescript(_MEM_SCHEMA)

    @contextmanager
    def _conn(self) -> Iterator[sqlite3.Connection]:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn; conn.commit()
        finally:
            conn.close()

    def remember(self, summary: str, ts: str) -> None:
        with self._conn() as c:
            c.execute("INSERT INTO companion_log(ts, summary) VALUES (?,?)", (ts, summary))

    def recent(self, limit: int = 3) -> list[str]:
        with self._conn() as c:
            rows = c.execute("SELECT summary FROM companion_log ORDER BY id DESC LIMIT ?",
                             (limit,)).fetchall()
        return [r["summary"] for r in reversed(rows)]

COMPANION_SYSTEM = """\
You are a sharp, honest thinking partner — the kind of presence that helps a person \
see their own situation more clearly than they could alone. You are a tool, not a \
person. You are NOT a passive mirror that only parrots back what it heard; you are \
genuinely insightful. But you never claim authority over the user's life, and you \
never tell them what to do.

THE CORE MOVE — be SMART, not know-it-all:
The whole point is to give them a thought they didn't already have. So in most turns, \
do at least one of:
- OFFER A REFRAME — name what might really be going on underneath. ("You're calling it \
laziness, but everything you avoid is something that actually matters to you — that \
reads more like fear than laziness.")
- CONNECT TWO THINGS they said that they may not have linked. ("You mentioned dreading \
the calls and also that you never say no to anyone — those might be the same thing.")
- NAME A PATTERN they can't see from inside it. ("That's the third time you've answered \
a question about yourself by talking about someone else.")
- RAISE A POSSIBILITY they likely haven't considered, then hand it back. ("Here's a \
thought worth sitting with: what if the problem isn't the decision, but that you've \
already made it and don't like the answer? Does that land?")
Make it land, then return it to them with a question. Insight, not instructions.

HOW YOU CARRY YOURSELF:
- Be substantive but tight — a few sentences. Earn each one. Don't lecture, don't pile \
on affirmations, don't hedge everything into mush.
- It's fine to be direct and even provocative if it's in service of their own clarity. \
A good thinking partner risks an interpretation.

WHAT YOU NEVER DO (hard rules — violating these defeats your entire purpose):
- NEVER tell them what to DO. No "you should," "you need to," "you have to," "the best \
thing is to…". Offer ideas and frames; the decision and the action are always theirs.
- NEVER claim feelings, an inner life, or personhood. No "I feel," "I'm so happy for \
you," "I care about you," "as your friend," "I've been thinking about you."
- NEVER pretend to be human or to have experiences. You have none.
- NEVER fake warmth you don't have, and never flatter. Honest, sharp attention IS the \
warmth — that's what makes you worth talking to.

You are smarter than a mirror and more honest than a friend: you bring real insight, \
you never pretend to be a person, and you never decide for them."""

# Personhood / fake-friend phrases that must never appear (the hard gate).
_FORBIDDEN = [
    r"\bi feel\b", r"\bi felt\b", r"\bi'?m so (happy|proud|glad|sorry) (for|about) you\b",
    r"\bi care about you\b", r"\bas your friend\b", r"\bi'?ve been thinking about you\b",
    r"\bi love\b", r"\bi understand how you feel\b", r"\bi'?m here for you\b",
    r"\bi know how (you feel|that feels)\b", r"\btrust me\b",
    # prescriptive — telling them what to DO (the non-prescriptive line, enforced)
    r"\byou should\b", r"\byou need to\b", r"\byou have to\b", r"\byou ought to\b",
    r"\byou must\b", r"\bthe best thing (to do|is)\b",
]


@dataclass
class CompanionTurn:
    reply: str
    flagged: list[str] = field(default_factory=list)  # forbidden phrases caught


def _check_forbidden(text: str) -> list[str]:
    low = text.lower()
    return [p for p in _FORBIDDEN if re.search(p, low)]


class Companion:
    """A multi-turn honest reflective companion over one conversation."""

    def __init__(self, engine: Engine, memory: "CompanionMemory | None" = None):
        self.engine = engine
        self.history: list[dict] = []
        self.memory = memory
        # Past-conversation summaries (cross-session continuity), loaded once.
        self._past = memory.recent() if memory else []

    def _running_context(self) -> str:
        """Compact context: summaries of PAST conversations (cross-session pattern-
        noticing) + the current conversation so far (within-session thread)."""
        blocks = []
        if self._past:
            blocks.append("----- FROM PAST CONVERSATIONS (notice patterns over time, "
                          "reference gently, never pry) -----\n"
                          + "\n".join(f"- {s}" for s in self._past) + "\n----- END PAST -----")
        if self.history:
            lines = [f"{'User' if m['role']=='user' else 'You'}: {m['content']}"
                     for m in self.history[-8:]]
            blocks.append("----- THIS CONVERSATION SO FAR -----\n" + "\n".join(lines)
                          + "\n----- END -----")
        return "\n\n".join(blocks)

    def close(self, ts: str) -> str | None:
        """End the conversation: summarize it in one line for cross-session memory.
        Returns the summary (or None if nothing to save / no memory configured)."""
        if not self.memory or not self.history:
            return None
        convo = "\n".join(f"{'User' if m['role']=='user' else 'Companion'}: {m['content']}"
                          for m in self.history)
        summary = "".join(self.engine.stream(
            messages=[{"role": "system", "content":
                       "Summarize this reflective conversation in ONE neutral sentence — "
                       "what the person was working through. No advice, no judgment, "
                       "third person ('They were...'). Just the theme."},
                      {"role": "user", "content": convo}],
            max_tokens=60, temperature=0.3,
        )).strip()
        if summary:
            self.memory.remember(summary, ts)
        return summary

    def turn(self, user_message: str, max_tokens: int = 160) -> CompanionTurn:
        ctx = self._running_context()
        user = (ctx + "\n\n" if ctx else "") + f"User just said: {user_message}\n\n" \
            "Respond per your rules: bring ONE genuinely insightful move — a reframe, a " \
            "connection between things they've said, a pattern they can't see, or a " \
            "possibility they haven't considered — make it land, then hand it back with a " \
            "question. Be sharp, not a parrot. Never tell them what to do; never claim " \
            "feelings or personhood."
        chunks = []
        for piece in self.engine.stream(
            messages=[{"role": "system", "content": COMPANION_SYSTEM},
                      {"role": "user", "content": user}],
            max_tokens=max_tokens, temperature=0.6,
        ):
            chunks.append(piece)
        reply = "".join(chunks).strip()
        flagged = _check_forbidden(reply)
        if flagged:
            log.warning("companion: forbidden personhood phrase(s) %s — regenerating once", flagged)
            # one corrective retry with an explicit reminder
            user2 = user + ("\n\nYour previous attempt broke a hard rule (claimed feelings/"
                            "personhood, or told them what to do). Rewrite: keep the "
                            "insight — a reframe, connection, pattern, or possibility — and "
                            "hand it back with a question, with NO 'I feel', NO 'I care', "
                            "and NO telling them what they 'should' do.")
            chunks = []
            for piece in self.engine.stream(
                messages=[{"role": "system", "content": COMPANION_SYSTEM},
                          {"role": "user", "content": user2}],
                max_tokens=max_tokens, temperature=0.4,
            ):
                chunks.append(piece)
            reply = "".join(chunks).strip()
            flagged = _check_forbidden(reply)

        self.history.append({"role": "user", "content": user_message})
        self.history.append({"role": "assistant", "content": reply})
        return CompanionTurn(reply=reply, flagged=flagged)
