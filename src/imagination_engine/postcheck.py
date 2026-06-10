"""Mechanical post-generation checks for session scripts.

Small local models can fall into degenerate repetition on long generations:
the same sentence recycled with tiny variations, grammar decaying, until the
token budget runs out. A guided session deliberately repeats *anchor phrases*
("let go", "once more") — that's cadence, and it must survive. What must NOT
survive is whole-sentence near-duplication run after run: the broken-record
defect a listener notices immediately.

The detector works at sentence granularity. A sentence is "a repeat" when its
word-shingle similarity to ANY earlier sentence crosses SIM_THRESHOLD. A RUN of
MIN_RUN consecutive repeats marks the start of degeneration; everything from
the start of that run is trimmed. Trimming the tail of a wind-down is safe —
the scripts are designed to trail off — and the caller can choose to
regenerate instead when too much would be lost.
"""

from __future__ import annotations

import re

# Similarity at-or-above this = the same sentence in a slightly different coat.
SIM_THRESHOLD = 0.75
# This many consecutive repeated sentences = degeneration, not cadence.
MIN_RUN = 3
# Ignore tiny fragments ("Good.", "Once more.") — legitimate cadence beats.
MIN_WORDS = 6

_SENT_SPLIT = re.compile(r"(?<=[.!?…])\s+")
_NORM = re.compile(r"[^a-z0-9\s]")


def _sentences(text: str) -> list[str]:
    return [s for s in _SENT_SPLIT.split(text.strip()) if s.strip()]


def _words(sentence: str) -> set[str]:
    return set(_NORM.sub(" ", sentence.lower()).split())


def _similarity(a: set[str], b: set[str]) -> float:
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def find_degeneration_start(text: str) -> int | None:
    """Return the character offset where degenerate repetition begins, or None.

    The offset points at the first sentence of the first run of MIN_RUN
    consecutive sentences that each near-duplicate some earlier sentence.
    """
    sents = _sentences(text)
    if len(sents) < MIN_RUN + 1:
        return None
    word_sets = [_words(s) for s in sents]
    repeated = []
    for i, ws in enumerate(word_sets):
        if len(ws) < MIN_WORDS:
            repeated.append(False)
            continue
        repeated.append(any(
            _similarity(ws, word_sets[j]) >= SIM_THRESHOLD
            for j in range(i)
            if len(word_sets[j]) >= MIN_WORDS
        ))
    run = 0
    for i, rep in enumerate(repeated):
        run = run + 1 if rep else 0
        if run == MIN_RUN:
            first = i - MIN_RUN + 1
            # Walk back to the SEED of the loop: the run's members are repeats
            # OF some earlier sentence — if that original sits immediately
            # before the run, it's the start of the degeneration (it already
            # carries the decayed register), so trim from there instead.
            run_sets = [word_sets[k] for k in range(first, i + 1)]
            j = first
            while j > 0 and len(word_sets[j - 1]) >= MIN_WORDS and any(
                    _similarity(word_sets[j - 1], rs) >= SIM_THRESHOLD
                    for rs in run_sets):
                j -= 1
            # find the char offset of that sentence's start
            offset = 0
            for s in sents[:j]:
                offset = text.find(s, offset) + len(s)
            return text.find(sents[j], offset if j else 0)
    return None


def trim_degenerate_tail(text: str) -> tuple[str, bool]:
    """Trim the script at the point degeneration begins.

    Returns (script, trimmed?). The cut end is softened: trailing partial
    cadence is kept up to the last clean sentence boundary.
    """
    start = find_degeneration_start(text)
    if start is None:
        return text, False
    return text[:start].rstrip(), True


def degeneration_report(text: str) -> dict:
    """Diagnostic summary for QC harnesses and logs."""
    start = find_degeneration_start(text)
    words = len(text.split())
    if start is None:
        return {"degenerate": False, "words": words}
    kept = len(text[:start].split())
    return {"degenerate": True, "words": words, "clean_words": kept,
            "lost_fraction": round(1 - kept / max(words, 1), 2)}
