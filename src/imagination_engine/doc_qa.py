"""Doc-Q&A — answer questions grounded in the user's own files.

The first real Family B/D FEATURE, assembled from the proven pieces: RAG retrieval
(rag.py, semantic-heavy, validated 100% top-1 on paraphrase queries) + the local
LLM (inference.py). The model answers ONLY from retrieved chunks of the user's
actual documents — so a small local model stays reliable (it transforms grounding
it can see, instead of recalling from memory where it hallucinates).

Flow: index files once → for each question, retrieve relevant chunks → put them in
the prompt as the ONLY source → the model answers from them, citing sources, and
says "not in your files" when the answer isn't there.

This is the engine under Family B (one-off "chat with this doc") and Family D (a
persistent "associate over my work files"). Local-first; nothing leaves the device.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path

from imagination_engine.inference import Engine
from imagination_engine.rag import RagStore, MLXEmbedder

log = logging.getLogger(__name__)

QA_SYSTEM = """\
You answer questions using ONLY the excerpts from the user's own files provided \
below. These excerpts are the ONLY source of truth — do not use outside knowledge.

RULES:
- Answer from the excerpts only. If the answer isn't in them, say plainly: "That \
isn't in your files." Do NOT guess or fill from general knowledge.
- Answer ONLY the question asked, then stop. Do not volunteer other facts from \
the excerpts, add commentary, or mention the files themselves.
- Be concise and direct. Quote or paraphrase the relevant excerpt.
- If the excerpts answer only part of the question, give the part that's there \
and say plainly which part isn't in your files. Nothing more.
- Never invent details, numbers, names, or events not in the excerpts."""


@dataclass
class Answer:
    text: str
    sources: list[str]
    grounded: bool  # did any chunk get retrieved at all?


class DocQA:
    """A grounded question-answerer over a named corpus of the user's files."""

    def __init__(self, engine: Engine, store: RagStore):
        self.engine = engine
        self.store = store

    @classmethod
    def open(cls, corpus_db: Path, engine: Engine | None = None,
             semantic: bool = True) -> "DocQA":
        embedder = MLXEmbedder() if semantic else None
        store = RagStore(corpus_db, embedder=embedder)
        return cls(engine or Engine.load(), store)

    def index(self, corpus: str, path: Path) -> dict:
        """Index a file or directory into the named corpus. One-time per corpus."""
        return self.store.index_path(corpus, Path(path))

    def ask(self, corpus: str, question: str, k: int = 5,
            max_tokens: int = 400) -> Answer:
        hits = self.store.retrieve(corpus, question, k=k)
        if not hits:
            return Answer("That isn't in your files (nothing indexed for this corpus yet).",
                          sources=[], grounded=False)
        grounding = self.store.context_block(corpus, question, k=k)
        sources = []
        for h in hits:
            name = Path(h.source).name
            if name not in sources:
                sources.append(name)
        user = (
            f"{grounding}\n\n"
            f"----- QUESTION -----\n{question}\n\n"
            "Answer using ONLY the excerpts above. Answer just this question, "
            'then stop. If the answer is not present, say "That isn\'t in your files."'
        )
        chunks = []
        for piece in self.engine.stream(
            messages=[{"role": "system", "content": QA_SYSTEM},
                      {"role": "user", "content": user}],
            max_tokens=max_tokens, temperature=0.2,  # low temp: faithful, not creative
        ):
            chunks.append(piece)
        return Answer("".join(chunks).strip(), sources=sources, grounded=True)
