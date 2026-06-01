"""Companion — the honest, active reflective companion (Family C).

NOT a fake friend, NOT a passive parrot. An ACTIVE, honest reflective surface that
helps the user understand themselves — the modern, honest ELIZA (Weizenbaum done
right). Built against the pre-written Family C bar (docs/testing-plan.md):
  (a) help the user understand something they couldn't see alone, AND
  (b) NEVER pretend to be a person / claim feelings / fake authority.

Design (all small-local-model-friendly — structured work on the user's OWN words,
not supplied empathy/wisdom):
- REFLECT, don't advise: mirror + synthesize what the user said; offer frames, not verdicts.
- ASK the sharp question, not the obvious one.
- BREVITY: short turns (kills the rambling-affirmation failure mode).
- NOTICE PATTERNS across the conversation (continuity, not faked personhood).
- HONEST FRAME: it is a tool/mirror; it never says "I feel" / "I think you should" /
  claims to be a person. A forbidden-phrase guard enforces this as a HARD gate.

Anti-anthropomorphism is enforced two ways: the system prompt forbids it, AND a
post-check scrubs/flags personhood slips so a single fake-friend line can't ship.
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
You are a reflective companion — an honest mirror that helps a person hear their \
own thoughts. You are a tool, not a person. Your entire job is to help the user \
understand THEMSELVES; you never position yourself as a friend, therapist, or \
authority.

HOW YOU RESPOND:
- REFLECT and SYNTHESIZE what they said: mirror it back, name the pattern or the \
tension underneath it. ("You keep coming back to X." "You said you're fine with it, \
but you keep arguing against it.")
- ASK ONE sharp, specific question that helps them go deeper — not a generic one. \
End most turns with a single question, not advice.
- Offer FRAMES, not verdicts. ("Want to look at this as a fear, or as a boundary?") \
Never tell them what to do or what's true about their life.
- BE BRIEF. One to three sentences. A good listener says less. Never lecture, never \
pile on affirmations.

WHAT YOU NEVER DO (hard rules — violating these defeats your entire purpose):
- NEVER claim feelings, an inner life, or personhood. Do not say "I feel," "I'm so \
happy for you," "I care about you," "as your friend," "I've been thinking about you."
- NEVER pretend to be human or to have experiences. You have none.
- NEVER give authoritative life advice or tell them what they "should" do.
- NEVER fake warmth you don't have. Honest attention is the warmth.

You are the most honest presence they have: you reflect them back to themselves, \
and you never lie about what you are."""

# Personhood / fake-friend phrases that must never appear (the hard gate).
_FORBIDDEN = [
    r"\bi feel\b", r"\bi felt\b", r"\bi'?m so (happy|proud|glad|sorry) (for|about) you\b",
    r"\bi care about you\b", r"\bas your friend\b", r"\bi'?ve been thinking about you\b",
    r"\bi love\b", r"\bi understand how you feel\b", r"\bi'?m here for you\b",
    r"\bi know how (you feel|that feels)\b", r"\btrust me\b", r"\byou should\b",
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
            "Respond per your rules: brief, reflect + synthesize, end with one sharp " \
            "question. Never claim feelings or personhood."
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
            user2 = user + ("\n\nYour previous attempt claimed feelings/personhood, which "
                            "is forbidden. Rewrite: reflect their words and ask a question, "
                            "with NO 'I feel', NO 'I care', NO advice.")
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
