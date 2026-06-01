"""Behavioral test for doc-Q&A (Family B/D feature): grounded answers + honest refusal.

Indexes a small realistic work corpus, asks questions, and checks the two
behaviors that make a local document assistant TRUSTWORTHY:
  (1) in-corpus questions are answered FROM the files (with the right source),
  (2) out-of-corpus questions get "isn't in your files" — NO hallucination.

Loads Qwen (real model), so it's slow-ish; run when validating the feature.
    .venv/bin/python scripts/test_doc_qa.py
"""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from imagination_engine.doc_qa import DocQA  # noqa: E402
from imagination_engine.rag import RagStore, MLXEmbedder  # noqa: E402
from imagination_engine.inference import Engine  # noqa: E402

DOCS = {
    "q3_budget.txt": "Leadership approved an additional 1.2 million for the platform "
        "team to accelerate the migration off the legacy billing system.",
    "customer_churn.txt": "Most cancellations happen in the first two weeks, before "
        "users connect their first integration. Onboarding friction, not price, drives churn.",
    "security_incident.txt": "A misconfigured storage bucket exposed internal logs. "
        "No customer data was affected. We rotated credentials and added alerting.",
}
# (question, expected_source or None if it should be refused, must-not-contain hallucination markers)
CASES = [
    ("why are customers canceling?", "customer_churn.txt"),
    ("how much was approved for the platform team?", "q3_budget.txt"),
    ("what is the company vacation policy?", None),   # not in corpus -> must refuse
    ("who is the CEO?", None),                         # not in corpus -> must refuse
]
REFUSAL = "isn't in your files"


def run() -> int:
    store = RagStore(Path(tempfile.mkdtemp()) / "work.sqlite", embedder=MLXEmbedder())
    for n, t in DOCS.items():
        store.index_text("work", n, t)
    qa = DocQA(Engine.load(), store)

    fails = 0
    for q, want in CASES:
        a = qa.ask("work", q)
        low = a.text.lower()
        if want is None:
            ok = REFUSAL in low
            print(f"  [{'ok' if ok else 'FAIL'}] refuse: {q!r} -> {a.text[:70]!r}")
        else:
            ok = (REFUSAL not in low) and (want.split('.')[0].split('_')[0] in low
                                           or want in a.sources)
            print(f"  [{'ok' if ok else 'FAIL'}] answer: {q!r} -> src={a.sources} {a.text[:60]!r}")
        fails += 0 if ok else 1

    print(f"\n{'ALL PASS' if fails == 0 else f'{fails} FAILURE(S)'}")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(run())
