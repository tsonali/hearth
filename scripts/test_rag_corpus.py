"""Behavioral RAG test on a REAL corpus (Pride & Prejudice, public domain).

Measures retrieval HIT-RATE against a labeled query set: each query has marker
phrases that the correct passage must contain. Reports top-1 / top-3 accuracy —
a real number to gauge embedder quality and to prove the eventual semantic-embedder
upgrade (re-run this; the score should jump).

Setup (one-time): the book lives at data/test_corpus/pride_and_prejudice.txt
  curl -sL https://www.gutenberg.org/files/1342/1342-0.txt -o data/test_corpus/pride_and_prejudice.txt

    .venv/bin/python scripts/test_rag_corpus.py
"""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from imagination_engine.rag import RagStore, MLXEmbedder, HashingEmbedder  # noqa: E402

BOOK = Path("data/test_corpus/pride_and_prejudice.txt")

# Labeled queries: query -> marker phrases the CORRECT passage should contain.
# IMPORTANT: every marker below is VERIFIED present in this Gutenberg edition
# (grep-confirmed) — a benchmark is only valid if the target text actually exists.
# (Lesson 2026-05-30: an earlier version used misremembered phrasings that weren't
# in the text, making good retrieval look broken. Verify labels against the corpus.)
LABELED = [
    ("Mr. Darcy's first proposal to Elizabeth that she refuses",
     ["in vain have I struggled"]),
    ("Elizabeth tells Darcy he is the last man she could be prevailed on to marry",
     ["last man in the world whom I could"]),
    ("Mr. Darcy snubs Elizabeth at the ball, calling her only tolerable",
     ["she is tolerable"]),
    ("the news that Netherfield Park has been let to a wealthy young man",
     ["Netherfield Park is let"]),
    ("Mr. Collins explains his reasons for wanting to marry",
     ["my reasons for marrying"]),
]


def run() -> int:
    if not BOOK.is_file():
        print(f"missing corpus: {BOOK}\n  fetch it (see this file's docstring).", file=sys.stderr)
        return 2
    use_semantic = "--lexical" not in sys.argv
    if use_semantic:
        print("embedder: MLXEmbedder (semantic, bge-small) — loading...")
        embedder = MLXEmbedder()
    else:
        print("embedder: HashingEmbedder (lexical baseline)")
        embedder = HashingEmbedder()
    store = RagStore(Path(tempfile.mkdtemp()) / "pp.sqlite", embedder=embedder)
    rep = store.index_path("pp", BOOK)
    print(f"indexed: {rep['chunks']} chunks from {BOOK.name}\n")

    top1 = top3 = 0
    for query, markers in LABELED:
        hits = store.retrieve("pp", query, k=3)
        def on_target(h):
            t = h.text.lower()
            return any(m.lower() in t for m in markers)
        hit1 = bool(hits) and on_target(hits[0])
        hit3 = any(on_target(h) for h in hits)
        top1 += hit1; top3 += hit3
        print(f"  [{'T1' if hit1 else ('t3' if hit3 else '--')}] {query[:55]}")

    n = len(LABELED)
    print(f"\n  top-1 accuracy: {top1}/{n} ({100*top1//n}%)")
    print(f"  top-3 accuracy: {top3}/{n} ({100*top3//n}%)")
    print(f"\n  (baseline = HashingEmbedder/lexical. Re-run after the semantic-embedder"
          f" swap; expect a jump. This is the RAG quality gauge.)")
    return 0


if __name__ == "__main__":
    sys.exit(run())
