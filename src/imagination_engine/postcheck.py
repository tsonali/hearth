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

# split after end punctuation followed by whitespace OR a bracket annotation
# (transcribed exemplars carry "[2.0]" pause marks straight after the period)
_SENT_SPLIT = re.compile(r"(?<=[.!?…])(?:\s+|(?=\[))")
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


# --- run-on collapse: the OTHER decay mode -----------------------------------
# Nothing repeats, but grammar disintegrates into an unpunctuated word-stream
# ("vast empty stretch Half Moon Bay's beach offers during this quietest time
# year where usually tourists flock instead remain few..."). Calibration against
# A_gold (2026-06-10) showed spoken-register gold legitimately runs 90+ word
# sentences with near-zero commas, so only the EXTREME tail is safely separable:
# the real catastrophe is 125w at 0.016 punctuation/word; the longest genuine
# gold sentence is 92w. Thresholds sit in the gap — this net catches only
# unambiguous salad, by design. Subtler decay is the fine-tune's job, not a
# regex's.
RUNON_WORDS = 110
RUNON_PUNCT_RATIO = 0.03

_PUNCT = re.compile(r"[,;:—–-]")


def _is_collapsed(sentence: str) -> bool:
    words = len(sentence.split())
    if words < RUNON_WORDS:
        return False
    punct = len(_PUNCT.findall(sentence))
    return (punct / words) < RUNON_PUNCT_RATIO


def _lines(text: str) -> list[str]:
    """Excision units: scripts mix '\\n\\n' paragraphs and single-'\\n' breaks;
    a line is the finest unit that can be dropped without orphaning syntax."""
    return text.split("\n")


def find_collapsed_paragraphs(text: str) -> list[int]:
    """Indices (line-granular) of units containing a run-on grammar collapse."""
    out = []
    for i, line in enumerate(_lines(text)):
        if any(_is_collapsed(s) for s in _sentences(line)):
            out.append(i)
    return out


def drop_collapsed_paragraphs(text: str) -> tuple[str, int]:
    """Remove collapsed lines. The moments in these long bodies are
    semi-independent, so excising one reads as a pause, not a hole — while a
    collapsed run-on read aloud shatters the session. Granularity is the LINE,
    not the blank-line paragraph: scripts that break with single newlines would
    otherwise lose good sentences along with the salad. Returns (text, n_dropped)."""
    lines = _lines(text)
    bad = set(find_collapsed_paragraphs(text))
    if not bad:
        return text, 0
    kept = [ln for i, ln in enumerate(lines) if i not in bad]
    out = "\n".join(kept)
    out = re.sub(r"\n{3,}", "\n\n", out).strip()
    return out, len(bad)


# --- non-adjacent verbatim repetition: the THIRD decay mode ------------------
# A long phrase recycled verbatim in two far-apart paragraphs (the grief-pet
# bench script repeated a ~50-word mystical tail twice). The consecutive-run
# detector can't see it; n-gram shingles can. Threshold: a 12-word verbatim
# shingle recurring outside its own paragraph. Calibrated against A_gold
# (anchor phrases are short; 12 words verbatim is machinery, not cadence).
NGRAM = 12


def find_phrase_repeats(text: str) -> list[tuple[int, int]]:
    """(first_para_idx, repeat_para_idx) pairs with a shared 12-word shingle."""
    paras = [p for p in re.split(r"\n+", text) if p.strip()]
    seen: dict[tuple, int] = {}
    out = []
    for i, para in enumerate(paras):
        words = _NORM.sub(" ", para.lower()).split()
        flagged = False
        for j in range(len(words) - NGRAM + 1):
            sh = tuple(words[j:j + NGRAM])
            if sh in seen and seen[sh] != i and not flagged:
                out.append((seen[sh], i))
                flagged = True  # one report per paragraph
            elif sh not in seen:
                seen[sh] = i
    return out


def phrase_repeat_count(text: str) -> int:
    """Count of repeated-shingle paragraph pairs. Heavily-recycled scripts
    (the grief-pet case: 18 pairs) are beyond surgical excision — this is a
    REPORT for the generation log and a CULL gate for the corpus, not an
    editing tool. In-product surgery can come later if data shows isolated
    single repeats are common."""
    return len(find_phrase_repeats(text))


def degeneration_report(text: str) -> dict:
    """Diagnostic summary for QC harnesses and logs."""
    start = find_degeneration_start(text)
    words = len(text.split())
    if start is None:
        return {"degenerate": False, "words": words}
    kept = len(text[:start].split())
    return {"degenerate": True, "words": words, "clean_words": kept,
            "lost_fraction": round(1 - kept / max(words, 1), 2)}
