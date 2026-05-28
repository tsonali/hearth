"""Local memory layer — SQLite store of completed sessions.

What this is:
    One row per completed session, persisted locally in SQLite. Holds the
    intake transcript, the generated script, when the user reflected and
    what they said, the voice that was used. Used by the intake conversation
    to weave in light references to past imaginings ("last time you worked
    on X — is this related, or something new?").

What this is NOT:
    A user-facing history. The user does NOT see a scrollable list of their
    own past sessions. The memory exists for the ENGINE — it shapes future
    intake conversations — not as a thread for the user to scroll. This
    preserves the "no thread to return to" design posture from build-plan/02.
    A history surface can come later if we change our minds; for v0 it stays
    invisible to the user.

Privacy:
    On-disk, gitignored, NEVER transmitted. The database lives only on the
    user's own machine. Storing data is the point — the value of the product
    compounds over time — but storage is local and the user retains full
    control (the file is at data/memory.sqlite; they can delete it).
"""

from __future__ import annotations

import json
import logging
import sqlite3
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterator, Optional

log = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Schema.
# ---------------------------------------------------------------------------

SCHEMA = """
CREATE TABLE IF NOT EXISTS sessions (
    id                  TEXT PRIMARY KEY,
    created_at          TEXT NOT NULL,           -- ISO 8601 UTC
    speaker             TEXT,                    -- e.g. 'sonali', 'julio'; NULL for Kokoro placeholder
    voice_backend       TEXT,                    -- 'kokoro' | 'f5'
    intake_prompt       TEXT,                    -- the user's first message — what they wanted to imagine
    intake_transcript   TEXT NOT NULL,           -- full conversation, JSON-encoded
    script              TEXT NOT NULL,           -- the generated session script (hidden thinking layer)
    script_word_count   INTEGER NOT NULL,
    reflection          TEXT,                    -- what they wrote after listening, may be NULL
    reflected_at        TEXT,                    -- ISO 8601 UTC, may be NULL
    duration_seconds    REAL                     -- audio duration, may be NULL
);

CREATE INDEX IF NOT EXISTS idx_sessions_created_at ON sessions(created_at DESC);
"""


# ---------------------------------------------------------------------------
# Row model.
# ---------------------------------------------------------------------------

@dataclass
class StoredSession:
    id: str
    created_at: str
    speaker: Optional[str]
    voice_backend: Optional[str]
    intake_prompt: str
    intake_transcript: list[dict]
    script: str
    script_word_count: int
    reflection: Optional[str]
    reflected_at: Optional[str]
    duration_seconds: Optional[float]


# ---------------------------------------------------------------------------
# The store.
# ---------------------------------------------------------------------------

class MemoryStore:
    """SQLite-backed memory of completed sessions. One per machine."""

    def __init__(self, db_path: Path):
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_schema()

    def _init_schema(self) -> None:
        with self._conn() as c:
            c.executescript(SCHEMA)

    @contextmanager
    def _conn(self) -> Iterator[sqlite3.Connection]:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()

    # -- writes -------------------------------------------------------------

    def save_session(
        self,
        *,
        session_id: str,
        intake_transcript: list[dict],
        script: str,
        voice_backend: str,
        speaker: str | None = None,
        duration_seconds: float | None = None,
    ) -> None:
        """Persist a completed session. Idempotent — re-saving the same id
        replaces the row (so re-generation overwrites cleanly)."""
        intake_prompt = ""
        for m in intake_transcript:
            if m.get("role") == "user" and (m.get("content", "") or "").strip():
                intake_prompt = m["content"].strip()
                break

        with self._conn() as c:
            c.execute(
                """
                INSERT INTO sessions (
                    id, created_at, speaker, voice_backend,
                    intake_prompt, intake_transcript,
                    script, script_word_count,
                    reflection, reflected_at, duration_seconds
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, NULL, NULL, ?)
                ON CONFLICT(id) DO UPDATE SET
                    created_at        = excluded.created_at,
                    speaker           = excluded.speaker,
                    voice_backend     = excluded.voice_backend,
                    intake_prompt     = excluded.intake_prompt,
                    intake_transcript = excluded.intake_transcript,
                    script            = excluded.script,
                    script_word_count = excluded.script_word_count,
                    duration_seconds  = excluded.duration_seconds
                """,
                (
                    session_id,
                    datetime.now(timezone.utc).isoformat(),
                    speaker,
                    voice_backend,
                    intake_prompt,
                    json.dumps(intake_transcript),
                    script,
                    len(script.split()),
                    duration_seconds,
                ),
            )
        log.info(
            "memory: saved session %s (%d-word script, voice=%s)",
            session_id, len(script.split()), voice_backend,
        )

    def capture_reflection(self, session_id: str, reflection: str) -> bool:
        """Record the user's post-session reflection. Returns True if a row was updated."""
        text = (reflection or "").strip()
        if not text:
            return False
        with self._conn() as c:
            cur = c.execute(
                "UPDATE sessions SET reflection = ?, reflected_at = ? WHERE id = ?",
                (text, datetime.now(timezone.utc).isoformat(), session_id),
            )
            updated = cur.rowcount > 0
        if updated:
            log.info("memory: captured reflection for %s (%d chars)", session_id, len(text))
        else:
            log.warning("memory: tried to capture reflection for unknown session %s", session_id)
        return updated

    # -- reads --------------------------------------------------------------

    def recent_sessions(self, limit: int = 3) -> list[StoredSession]:
        """Most recently completed sessions, newest first."""
        with self._conn() as c:
            rows = c.execute(
                """
                SELECT id, created_at, speaker, voice_backend,
                       intake_prompt, intake_transcript, script, script_word_count,
                       reflection, reflected_at, duration_seconds
                FROM sessions
                ORDER BY created_at DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
        out: list[StoredSession] = []
        for r in rows:
            try:
                transcript = json.loads(r["intake_transcript"]) if r["intake_transcript"] else []
            except json.JSONDecodeError:
                transcript = []
            out.append(
                StoredSession(
                    id=r["id"],
                    created_at=r["created_at"],
                    speaker=r["speaker"],
                    voice_backend=r["voice_backend"],
                    intake_prompt=r["intake_prompt"] or "",
                    intake_transcript=transcript,
                    script=r["script"] or "",
                    script_word_count=r["script_word_count"] or 0,
                    reflection=r["reflection"],
                    reflected_at=r["reflected_at"],
                    duration_seconds=r["duration_seconds"],
                )
            )
        return out

    def count(self) -> int:
        with self._conn() as c:
            return c.execute("SELECT COUNT(*) AS n FROM sessions").fetchone()["n"]

    # -- context formatting -------------------------------------------------

    def format_for_intake_context(self, limit: int = 2) -> str:
        """A compact text block describing recent sessions, for the intake system prompt.

        Returns "" if there's no history — intake operates fresh on first use.
        """
        sessions = self.recent_sessions(limit=limit)
        if not sessions:
            return ""

        now = datetime.now(timezone.utc)
        lines: list[str] = []
        for s in sessions:
            try:
                ts = datetime.fromisoformat(s.created_at)
                delta = now - ts
                if delta.days < 1:
                    when = "earlier today" if delta.seconds < 12 * 3600 else "today"
                elif delta.days == 1:
                    when = "yesterday"
                elif delta.days < 7:
                    when = f"{delta.days} days ago"
                elif delta.days < 30:
                    when = f"{delta.days // 7} weeks ago"
                else:
                    when = f"{delta.days // 30} months ago"
            except Exception:
                when = s.created_at[:10]

            reflection_part = f"\n    Reflection: {s.reflection.strip()}" if s.reflection else ""
            lines.append(f"- {when}: \"{s.intake_prompt}\"{reflection_part}")

        return (
            "PAST SESSIONS — recent imaginings the user has done. Use this lightly:\n"
            + "\n".join(lines)
            + "\n\nReference these naturally ONLY if relevant to what they're bringing today. "
            "Don't list them. Don't quiz them. A single light line like "
            "'Last time you worked on X — is this related, or something new?' is the right touch. "
            "If today's imagining has nothing to do with past ones, don't mention them at all."
        )
