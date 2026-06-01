"""Behavioral RAG test on the REAL use case: paraphrase queries over a doc set.

The P&P benchmark tests exact-phrase lookup (lexical's home turf) — but real users
ask "what did we decide about the budget?" over their OWN files, where the answer is
NOT worded like the question. THIS test matches that: a realistic synthetic "work
corpus" (meeting notes / emails / docs) + queries that paraphrase the content. This
is where semantic retrieval should beat lexical — the honest gauge for Family B/D.

    .venv/bin/python scripts/test_rag_paraphrase.py            # hybrid (default)
    .venv/bin/python scripts/test_rag_paraphrase.py --lexical  # lexical-only
    .venv/bin/python scripts/test_rag_paraphrase.py --semantic # semantic-only
"""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from imagination_engine.rag import RagStore, MLXEmbedder, HashingEmbedder  # noqa: E402

# A realistic personal "work corpus." Each doc has a clear topic; queries below
# PARAPHRASE the content (different words than the doc) — the real-use scenario.
DOCS = {
    "q3_budget.txt":
        "Following the finance review, leadership approved an additional 1.2 million "
        "for the platform team to accelerate the migration off the legacy billing "
        "system before the holiday freeze.",
    "hiring_update.txt":
        "We extended an offer to the senior infrastructure candidate who impressed "
        "everyone with her work on fault-tolerant distributed queues. She starts in "
        "three weeks and will lead the reliability initiative.",
    "customer_churn.txt":
        "The retention analysis showed most cancellations happen in the first two "
        "weeks, before users connect their first integration. Onboarding friction, "
        "not price, is driving people away.",
    "office_move.txt":
        "The team will relocate to the new space on Howard Street in October. It has "
        "more meeting rooms and a quiet floor for focused work; parking is limited so "
        "transit passes will be subsidized.",
    "security_incident.txt":
        "A misconfigured storage bucket briefly exposed internal logs. No customer "
        "data was affected. We rotated the credentials, added alerting, and scheduled "
        "a full access-control audit for next month.",
}

# query (paraphrased — NOT using the doc's words) -> which doc SHOULD be top hit
LABELED = [
    ("how much extra money did we put toward the engineering work", "q3_budget.txt"),
    ("who are we bringing on to improve system uptime", "hiring_update.txt"),
    ("why are people canceling their subscriptions", "customer_churn.txt"),
    ("where is the company relocating and how do we get there", "office_move.txt"),
    ("did the data leak hurt any of our users", "security_incident.txt"),
    ("what's the main reason new signups don't stick around", "customer_churn.txt"),
]


def run() -> int:
    mode = "hybrid"
    if "--lexical" in sys.argv: mode = "lexical"
    elif "--semantic" in sys.argv: mode = "semantic"
    print(f"mode: {mode}")
    emb = HashingEmbedder() if mode == "lexical" else MLXEmbedder()
    store = RagStore(Path(tempfile.mkdtemp()) / "work.sqlite", embedder=emb)
    for name, text in DOCS.items():
        store.index_text("work", name, text)

    alpha = {"hybrid": 0.6, "semantic": 1.0, "lexical": 0.0}[mode]
    top1 = top3 = 0
    for q, want in LABELED:
        hits = store.retrieve("work", q, k=3, alpha=alpha)
        names = [Path(h.source).name for h in hits]
        h1 = bool(names) and names[0] == want
        h3 = want in names
        top1 += h1; top3 += h3
        print(f"  [{'T1' if h1 else ('t3' if h3 else '--')}] {q[:48]:48}  -> {names[0] if names else '?'}")
    n = len(LABELED)
    print(f"\n  top-1: {top1}/{n} ({100*top1//n}%)   top-3: {top3}/{n} ({100*top3//n}%)")
    print("  (paraphrase queries over a work corpus = the REAL Family B/D use case)")
    return 0


if __name__ == "__main__":
    sys.exit(run())
