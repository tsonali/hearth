"""Tests for the RAG layer (the shared engine under Family B + D).

Proves the plumbing end-to-end with the dependency-free HashingEmbedder: chunk →
index → retrieve-the-right-thing → format grounding. (Semantic quality awaits a
real on-device embedder; this proves the store/retrieval/grounding pipeline.)

    .venv/bin/python scripts/test_rag.py
"""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from imagination_engine.rag import RagStore, chunk_text  # noqa: E402


def run() -> int:
    fails = 0
    def check(name, cond, detail=""):
        nonlocal fails
        print(f"  [{'ok' if cond else 'FAIL'}] {name}" + (f" — {detail}" if detail and not cond else ""))
        fails += 0 if cond else 1

    print("== chunking ==")
    long = "\n\n".join(f"Paragraph {i} about topic {i}. " * 20 for i in range(6))
    chunks = chunk_text(long, target_words=100, overlap_words=20)
    check("splits long text into multiple chunks", len(chunks) > 1, f"{len(chunks)} chunks")
    check("chunks are non-empty", all(c.strip() for c in chunks))

    with tempfile.TemporaryDirectory() as td:
        db = Path(td) / "rag.sqlite"
        store = RagStore(db)

        # a tiny personal corpus: three "files" on different topics
        store.index_text("work", "march_planning.txt",
            "In the March planning meeting we decided to delay the Helsinki launch "
            "until Q3 and to hire two backend engineers. Budget approved at 1.2M.")
        store.index_text("work", "vacation.txt",
            "Notes on my trip to Portugal: the train from Lisbon to Porto, the pastries, "
            "the tile museum, swimming at the beach near Cascais.")
        store.index_text("work", "hiring.txt",
            "Candidate pipeline: three backend interviews scheduled. Priya strong on "
            "distributed systems. Final decision after the March planning outcome.")

        print("== index ==")
        stats = store.corpus_stats("work")
        check("indexed 3 sources", stats["sources"] == 3, str(stats))
        check("created chunks", stats["chunks"] >= 3, str(stats))

        print("== retrieve (lexical overlap; the right doc should rank top) ==")
        hits = store.retrieve("work", "what did we decide about the Helsinki launch and budget", k=3)
        check("got results", len(hits) >= 1)
        top = Path(hits[0].source).name if hits else ""
        check("Helsinki/budget query -> march_planning.txt on top",
              top == "march_planning.txt", f"top was {top}")

        hits2 = store.retrieve("work", "where did I swim on my trip", k=3)
        top2 = Path(hits2[0].source).name if hits2 else ""
        check("swim/trip query -> vacation.txt on top", top2 == "vacation.txt", f"top was {top2}")

        print("== grounding block ==")
        block = store.context_block("work", "who is strong on distributed systems", k=2)
        check("grounding block names the source + content",
              "hiring.txt" in block and "Priya" in block, block[:120])

        print("== corpus isolation ==")
        store.index_text("personal", "diary.txt", "Today I felt anxious about the dentist.")
        h = store.retrieve("work", "dentist anxiety", k=3)
        check("'work' corpus does not return 'personal' chunks",
              all("diary.txt" not in r.source for r in h))

    print(f"\n{'ALL PASS' if fails == 0 else f'{fails} FAILURE(S)'}")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(run())
