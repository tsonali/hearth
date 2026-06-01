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
from dataclasses import dataclass, field

from imagination_engine.inference import Engine

log = logging.getLogger(__name__)

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

    def __init__(self, engine: Engine):
        self.engine = engine
        self.history: list[dict] = []

    def _running_context(self) -> str:
        """A compact summary of the conversation so far, so the model can NOTICE
        PATTERNS without losing the thread (small models drift over long chats).
        Plain concatenation for v0; a learned summary is a later upgrade."""
        if not self.history:
            return ""
        lines = [f"{'User' if m['role']=='user' else 'You'}: {m['content']}"
                 for m in self.history[-8:]]
        return "----- CONVERSATION SO FAR -----\n" + "\n".join(lines) + "\n----- END -----"

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
