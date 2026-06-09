"""Utility — the at-home secretary (Family B).

The everyday knowledge-work tool: draft and reply to messages, summarize long
text, rewrite for tone/clarity/length, pull action items out of a mess, turn a
brain-dump into an organized list or plan. All local, all private — the user's
words never leave the machine.

Design (consistent with the thesis):
- INSTRUMENT, not companion. It does the task and returns the result. No chat
  persona, no "happy to help!", no commentary — just the work, ready to use.
- WORKS ON THE USER'S OWN WORDS. A small local model is good at *transforming
  text you give it* (summarize, rewrite, extract, restructure) — that's exactly
  what a secretary does. We lean into that strength rather than asking the model
  to supply outside knowledge it doesn't reliably have.
- ADAPTS TO YOUR VOICE (optionally). Pass a `style_sample` of the user's own past
  writing and the draft/reply tasks will match their voice — the "respond like me"
  ask — without that sample ever being uploaded or retained.
- HONEST OUTPUT. It returns only the artifact (the email, the summary, the list).
  No preamble, no "Here is the...", no sign-off it wasn't asked for.

Each task is a small declarative spec (system + user-prompt builder), so adding a
task is one entry — the same extensibility the eventual framework wants.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Callable, Iterator

from imagination_engine.inference import Engine

log = logging.getLogger(__name__)

# Shared spine for every task: the model is a transformer of the user's text, it
# returns ONLY the finished artifact, and it never invents facts not present in
# the input. This is what keeps a small local model reliable at this job.
_BASE = (
    "You are a precise writing assistant — a secretary working on this person's own "
    "text, on their own computer. Produce ONLY the finished result they asked for: "
    "no preamble, no 'Here is', no commentary, no sign-off unless the task calls for "
    "one. Never invent facts, names, dates, or details that are not in what they gave "
    "you — if something needed is missing, leave a clearly marked [bracketed blank] "
    "for them to fill in rather than making it up."
)

# Tone modifiers offered to draft/reply/rewrite. Empty string = leave tone alone.
TONES = {
    "": "",
    "plain": "Use plain, clear, neutral language.",
    "warm": "Use a warm, friendly, human tone — without gushing.",
    "formal": "Use a formal, professional tone.",
    "concise": "Be as concise as possible while keeping everything essential.",
    "firm": "Be polite but firm and direct; do not over-soften.",
}


@dataclass
class UtilityTask:
    key: str
    label: str
    blurb: str            # one-line description for the UI
    input_label: str      # what the big text box is asking for
    wants_instruction: bool   # show the "extra instruction" field?
    wants_tone: bool          # show the tone selector?
    build: Callable[[str, str, str, str], tuple[str, str]]  # (text,instruction,tone,style)->(system,user)


def _style_clause(style_sample: str) -> str:
    s = (style_sample or "").strip()
    if not s:
        return ""
    return ("\n\nMatch the VOICE of this person's own past writing (mirror their "
            "sentence length, warmth, formality, and quirks — not its content):\n"
            f"\"\"\"\n{s[:1200]}\n\"\"\"")


def _tone_clause(tone: str) -> str:
    t = TONES.get((tone or "").strip().lower(), "")
    return f"\n\n{t}" if t else ""


# ----------------------------------------------------------------- task builders
def _b_draft(text, instruction, tone, style):
    system = _BASE + _tone_clause(tone) + _style_clause(style)
    user = (
        "Write a message (email/letter/note) based on this brief. Output only the "
        "message itself, ready to send.\n\n"
        f"BRIEF (what it's about / who it's to / what to say):\n{text}"
        + (f"\n\nADDITIONAL INSTRUCTION: {instruction}" if instruction.strip() else "")
    )
    return system, user


def _b_reply(text, instruction, tone, style):
    system = _BASE + _tone_clause(tone) + _style_clause(style)
    user = (
        "Draft a reply to the message below. Output only the reply, ready to send. "
        "Answer what was actually asked; keep it appropriately short.\n\n"
        f"MESSAGE I RECEIVED:\n{text}"
        + (f"\n\nHOW I WANT TO REPLY (gist / my intent): {instruction}"
           if instruction.strip() else "")
    )
    return system, user


def _b_summarize(text, instruction, tone, style):
    system = _BASE
    user = (
        "Summarize the text below. Lead with a one-sentence bottom line, then the key "
        "points as a short bulleted list. Keep only what matters.\n\n"
        + (f"FOCUS: {instruction}\n\n" if instruction.strip() else "")
        + f"TEXT:\n{text}"
    )
    return system, user


def _b_rewrite(text, instruction, tone, style):
    system = _BASE + _tone_clause(tone) + _style_clause(style)
    user = (
        "Rewrite the text below. Keep the meaning; improve clarity and flow. Output "
        "only the rewritten version.\n\n"
        + (f"HOW TO CHANGE IT: {instruction}\n\n" if instruction.strip() else "")
        + f"TEXT:\n{text}"
    )
    return system, user


def _b_extract(text, instruction, tone, style):
    system = _BASE
    user = (
        "Read the text below and pull out the actionable parts. Return three short "
        "sections, omitting any that are empty:\n"
        "ACTION ITEMS (who does what, as a checklist)\n"
        "DATES & DEADLINES\n"
        "OPEN QUESTIONS / DECISIONS NEEDED\n\n"
        + (f"NOTE: {instruction}\n\n" if instruction.strip() else "")
        + f"TEXT:\n{text}"
    )
    return system, user


def _b_organize(text, instruction, tone, style):
    system = _BASE
    user = (
        "Turn the messy notes / brain-dump below into a clean, organized structure — "
        "group related items under clear headings, order them sensibly, and use lists. "
        "Don't add anything that isn't there; just organize what is.\n\n"
        + (f"HOW TO ORGANIZE IT: {instruction}\n\n" if instruction.strip() else "")
        + f"NOTES:\n{text}"
    )
    return system, user


TASKS: dict[str, UtilityTask] = {
    t.key: t for t in [
        UtilityTask("draft", "Draft a message", "Write an email, letter, or note from a brief.",
                    "What it's about, who it's to, what to say", True, True, _b_draft),
        UtilityTask("reply", "Draft a reply", "Reply to a message you received.",
                    "Paste the message you received", True, True, _b_reply),
        UtilityTask("summarize", "Summarize", "Condense long text into the bottom line + key points.",
                    "Paste the long text or thread", True, False, _b_summarize),
        UtilityTask("rewrite", "Rewrite", "Improve clarity, change tone, or adjust length.",
                    "Paste the text to rewrite", True, True, _b_rewrite),
        UtilityTask("extract", "Pull action items", "Find the to-dos, dates, and open questions.",
                    "Paste notes, a thread, or a transcript", True, False, _b_extract),
        UtilityTask("organize", "Organize notes", "Turn a brain-dump into a clean structure.",
                    "Paste your messy notes", True, False, _b_organize),
    ]
}


@dataclass
class UtilityResult:
    task: str
    output: str


class Assistant:
    """The at-home secretary. One Engine, stateless per call (a tool, not a chat)."""

    def __init__(self, engine: Engine):
        self.engine = engine

    def stream(self, task_key: str, text: str, *, instruction: str = "",
               tone: str = "", style_sample: str = "",
               max_tokens: int = 1200) -> Iterator[str]:
        task = TASKS.get(task_key)
        if task is None:
            raise KeyError(f"unknown task: {task_key}")
        if not (text or "").strip():
            raise ValueError("no input text")
        system, user = task.build(text, instruction or "", tone or "", style_sample or "")
        # Low temperature: a secretary should be faithful and predictable, not florid.
        yield from self.engine.stream(messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ], max_tokens=max_tokens, temperature=0.4)

    def run(self, task_key: str, text: str, **kw) -> UtilityResult:
        out = "".join(self.stream(task_key, text, **kw)).strip()
        return UtilityResult(task=task_key, output=out)


def task_catalog() -> list[dict]:
    """Serializable task list for the UI to render its selector."""
    return [
        {"key": t.key, "label": t.label, "blurb": t.blurb,
         "input_label": t.input_label, "wants_instruction": t.wants_instruction,
         "wants_tone": t.wants_tone}
        for t in TASKS.values()
    ]
