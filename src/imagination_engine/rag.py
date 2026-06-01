"""RAG — retrieval over the user's own files. A FRAMEWORK-GENERAL primitive.

The shared engine under Family B (one-off doc-Q&A) and Family D (the persistent,
personal "associate over my work files / email"). Everything here is local-first
and private by construction: files are read, chunked, embedded, and indexed ON the
user's machine, into a local SQLite store, and NOTHING leaves the device — same
privacy posture as memory.py and the rest of the engine.

DESIGN (deliberately simple, swappable):
- **Chunking:** split documents into overlapping windows (paragraph-aware), so a
  retrieved chunk is a coherent passage, not a fragment.
- **Embeddings:** an on-device embedding model turns each chunk into a vector.
  The embedder is a seam (`Embedder`) so we can swap models without touching the
  store. v0 ships a deterministic hashing embedder as a no-dependency fallback so
  the module is testable + runnable TODAY; a real MLX/sentence-transformers
  embedder drops in behind the same interface.
- **Store:** SQLite (mirrors memory.py) holding chunks + their vectors. Retrieval
  is cosine similarity over the vectors. For the personal-corpus scale we target
  (a person's files, not the web), brute-force cosine in SQLite is plenty fast;
  a vector index (faiss/sqlite-vec) is a later optimization behind the same API.

This makes a SMALL local model reliable on document tasks: the model never recalls
from memory (where it hallucinates) — it answers grounded in retrieved chunks of
the user's actual files (the research: RAG drove hallucination ~0%).
"""

from __future__ import annotations

import hashlib
import math
import re
import sqlite3
import struct
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator, Protocol

# ---------------------------------------------------------------------------
# Embedder seam — swap the implementation without touching the store.
# ---------------------------------------------------------------------------

class Embedder(Protocol):
    dim: int
    def embed(self, texts: list[str]) -> list[list[float]]: ...


class HashingEmbedder:
    """Dependency-free, deterministic fallback embedder (bag-of-hashed-tokens).

    NOT semantically strong — it captures lexical overlap, not deep meaning. Its
    job is to make the whole RAG pipeline runnable + testable with zero model
    downloads, and to prove the store/retrieval plumbing. Swap in a real on-device
    embedding model (MLX / sentence-transformers) behind the same .embed() for
    production semantic retrieval.
    """
    def __init__(self, dim: int = 256):
        self.dim = dim

    def embed(self, texts: list[str]) -> list[list[float]]:
        out = []
        for t in texts:
            vec = [0.0] * self.dim
            for tok in re.findall(r"[a-z0-9']+", t.lower()):
                h = int(hashlib.md5(tok.encode()).hexdigest(), 16)
                vec[h % self.dim] += 1.0
            out.append(_l2_normalize(vec))
        return out


class MLXEmbedder:
    """Real semantic embedder — on-device via mlx-embeddings (Apple Silicon).

    Default model bge-small-en-v1.5 (384-dim, Apache/MIT-lineage, ~130MB) produces
    genuine semantic embeddings: "anxious about the dentist" matches "nervous" even
    with no shared words — the thing HashingEmbedder can't do. Lazy-loaded so the
    module imports without the dep; pass an instance to RagStore to use it.
    Outputs are L2-normalized (cosine = dot product, same as the store expects).
    """
    def __init__(self, model_id: str = "mlx-community/bge-small-en-v1.5-bf16",
                 batch_size: int = 32):
        from mlx_embeddings import load
        self._load = load
        self.model_id = model_id
        self.batch_size = batch_size
        self.model, self.tokenizer = load(model_id)
        self.dim = 384

    def embed(self, texts: list[str]) -> list[list[float]]:
        from mlx_embeddings import generate
        out: list[list[float]] = []
        for i in range(0, len(texts), self.batch_size):
            batch = texts[i:i + self.batch_size]
            emb = generate(self.model, self.tokenizer, texts=batch).text_embeds
            for row in emb.tolist():
                out.append(_l2_normalize(row))  # ensure unit norm for cosine
        return out


def _l2_normalize(v: list[float]) -> list[float]:
    n = math.sqrt(sum(x * x for x in v)) or 1.0
    return [x / n for x in v]


def _cosine(a: list[float], b: list[float]) -> float:
    return sum(x * y for x, y in zip(a, b))  # both pre-normalized


# ---------------------------------------------------------------------------
# Chunking — paragraph-aware overlapping windows.
# ---------------------------------------------------------------------------

def chunk_text(text: str, *, target_words: int = 220, overlap_words: int = 40) -> list[str]:
    """Split into coherent overlapping passages. Prefers paragraph boundaries;
    falls back to word windows for long unbroken text."""
    paras = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    chunks: list[str] = []
    buf: list[str] = []
    count = 0
    for para in paras:
        w = para.split()
        if count + len(w) > target_words and buf:
            chunks.append(" ".join(buf))
            # carry overlap from the tail of the previous chunk
            tail = " ".join(buf).split()[-overlap_words:]
            buf = tail[:]
            count = len(tail)
        buf.extend(w)
        count += len(w)
    if buf:
        chunks.append(" ".join(buf))
    return chunks or ([text.strip()] if text.strip() else [])


# ---------------------------------------------------------------------------
# Store — local SQLite, vectors as blobs. Mirrors memory.py's posture.
# ---------------------------------------------------------------------------

_SCHEMA = """
CREATE TABLE IF NOT EXISTS chunks (
    id        INTEGER PRIMARY KEY AUTOINCREMENT,
    corpus    TEXT NOT NULL,           -- named instrument/corpus (Family D: "work-associate")
    source    TEXT NOT NULL,           -- file path the chunk came from
    ordinal   INTEGER NOT NULL,        -- chunk index within the source
    text      TEXT NOT NULL,
    vector    BLOB NOT NULL,           -- float32 array
    dim       INTEGER NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_chunks_corpus ON chunks(corpus);
"""


@dataclass
class Retrieved:
    text: str
    source: str
    score: float


def _pack(v: list[float]) -> bytes:
    return struct.pack(f"{len(v)}f", *v)


def _unpack(b: bytes, dim: int) -> list[float]:
    return list(struct.unpack(f"{dim}f", b))


class RagStore:
    """A local, private retrieval index over the user's files."""

    def __init__(self, db_path: Path, embedder: Embedder | None = None):
        self.db_path = db_path
        self.embedder = embedder or HashingEmbedder()
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        with self._conn() as c:
            c.executescript(_SCHEMA)

    @contextmanager
    def _conn(self) -> Iterator[sqlite3.Connection]:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()

    def index_text(self, corpus: str, source: str, text: str) -> int:
        """Chunk + embed a document's text and store it. Returns #chunks added."""
        chunks = chunk_text(text)
        if not chunks:
            return 0
        vecs = self.embedder.embed(chunks)
        with self._conn() as c:
            for i, (ch, v) in enumerate(zip(chunks, vecs)):
                c.execute(
                    "INSERT INTO chunks(corpus, source, ordinal, text, vector, dim) "
                    "VALUES (?,?,?,?,?,?)",
                    (corpus, source, i, ch, _pack(v), len(v)),
                )
        return len(chunks)

    def index_path(self, corpus: str, path: Path,
                   exts: tuple[str, ...] = (".txt", ".md")) -> dict:
        """Index a file or a directory tree (text files for v0). Returns a report."""
        path = Path(path)
        files = [path] if path.is_file() else [
            p for p in path.rglob("*") if p.is_file() and p.suffix.lower() in exts
        ]
        added = 0
        for f in files:
            try:
                added += self.index_text(corpus, str(f), f.read_text(encoding="utf-8", errors="ignore"))
            except Exception:
                continue
        return {"files": len(files), "chunks": added, "corpus": corpus}

    def retrieve(self, corpus: str, query: str, k: int = 5) -> list[Retrieved]:
        """Return the top-k most relevant chunks for the query, by cosine sim."""
        qv = self.embedder.embed([query])[0]
        with self._conn() as c:
            rows = c.execute(
                "SELECT source, text, vector, dim FROM chunks WHERE corpus=?", (corpus,)
            ).fetchall()
        scored = [
            Retrieved(text=r["text"], source=r["source"],
                      score=_cosine(qv, _unpack(r["vector"], r["dim"])))
            for r in rows
        ]
        scored.sort(key=lambda x: -x.score)
        return scored[:k]

    def context_block(self, corpus: str, query: str, k: int = 5) -> str:
        """Retrieved chunks formatted for injection into a generation prompt —
        the grounding the model answers FROM (so it doesn't hallucinate)."""
        hits = self.retrieve(corpus, query, k=k)
        if not hits:
            return ""
        parts = ["----- RELEVANT EXCERPTS FROM YOUR FILES (answer ONLY from these) -----"]
        for i, h in enumerate(hits, 1):
            src = Path(h.source).name
            parts.append(f"[{i}] (from {src})\n{h.text}")
        parts.append("----- END EXCERPTS -----")
        return "\n\n".join(parts)

    def corpus_stats(self, corpus: str) -> dict:
        with self._conn() as c:
            n = c.execute("SELECT COUNT(*) FROM chunks WHERE corpus=?", (corpus,)).fetchone()[0]
            srcs = c.execute("SELECT COUNT(DISTINCT source) FROM chunks WHERE corpus=?", (corpus,)).fetchone()[0]
        return {"corpus": corpus, "chunks": n, "sources": srcs}
