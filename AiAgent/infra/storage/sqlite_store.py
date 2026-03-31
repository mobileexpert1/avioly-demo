from __future__ import annotations
import json
import math
import sqlite3
import struct
import re
from pathlib import Path

from ...core.interfaces import DocumentStore, VectorStore
from ...core.types import RetrievedChunk

class SQLiteDocumentVectorStore(DocumentStore, VectorStore):
    def __init__(self, path: Path):
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    def _initialize(self) -> None:
        with sqlite3.connect(self.path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS chunks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    collection_id TEXT NOT NULL,
                    document_name TEXT NOT NULL,
                    chunk_index INTEGER NOT NULL,
                    text TEXT NOT NULL,
                    metadata TEXT,
                    embedding BLOB NOT NULL
                )
                """
            )
            columns = [row[1] for row in conn.execute("PRAGMA table_info(chunks)").fetchall()]
            if "embedding" not in columns:
                try:
                    conn.execute("ALTER TABLE chunks ADD COLUMN embedding BLOB")
                except sqlite3.OperationalError as exc:
                    if "duplicate column name" not in str(exc).lower():
                        raise
                conn.execute("UPDATE chunks SET embedding = X'' WHERE embedding IS NULL")

    def save_chunks(self, collection_id: str, chunks: list[RetrievedChunk]) -> None:
        """No-op as upsert handles both text and embeddings in one go for SQLite."""
        pass

    def list_documents(self, collection_id: str) -> list[str]:
        with sqlite3.connect(self.path) as conn:
            rows = conn.execute(
                "SELECT DISTINCT document_name FROM chunks WHERE collection_id = ? ORDER BY document_name",
                (collection_id,),
            ).fetchall()
        return [row[0] for row in rows]

    def upsert(self, collection_id: str, chunks: list[RetrievedChunk], embeddings: list[list[float]]) -> None:
        with sqlite3.connect(self.path) as conn:
            conn.execute("DELETE FROM chunks WHERE collection_id = ?", (collection_id,))
            for chunk, embedding in zip(chunks, embeddings, strict=True):
                conn.execute(
                    """
                    INSERT INTO chunks (collection_id, document_name, chunk_index, text, metadata, embedding)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        chunk.source_id,
                        chunk.document_name,
                        chunk.chunk_index,
                        chunk.text,
                        self._metadata_json(chunk),
                        self._pack_embedding(embedding),
                    ),
                )

    def search(self, collection_id: str, query: str, query_embedding: list[float], limit: int = 5) -> list[RetrievedChunk]:
        query_terms = {term.lower() for term in re.findall(r"[A-Za-z0-9]+", query) if len(term) > 2}
        with sqlite3.connect(self.path) as conn:
            rows = conn.execute(
                """
                SELECT document_name, chunk_index, text, metadata, embedding
                FROM chunks
                WHERE collection_id = ?
                """,
                (collection_id,),
            ).fetchall()

        scored: list[RetrievedChunk] = []
        for document_name, chunk_index, text, metadata_json, embedding_blob in rows:
            stored_embedding = self._unpack_embedding(embedding_blob)
            cosine = self._cosine_similarity(query_embedding, stored_embedding)
            lexical = self._lexical_score(query_terms, text)
            score = (0.7 * cosine) + (0.3 * lexical)
            scored.append(
                RetrievedChunk(
                    source_id=collection_id,
                    document_name=document_name,
                    chunk_index=chunk_index,
                    text=text,
                    score=score,
                    metadata=json.loads(metadata_json) if metadata_json else None,
                )
            )

        scored.sort(key=lambda item: item.score, reverse=True)
        return scored[:limit]

    def _metadata_json(self, chunk: RetrievedChunk) -> str | None:
        if not chunk.metadata: return None
        return json.dumps(chunk.metadata, sort_keys=True)

    def _pack_embedding(self, embedding: list[float]) -> bytes:
        return struct.pack(f"{len(embedding)}f", *embedding)

    def _unpack_embedding(self, blob: bytes) -> list[float]:
        if not blob: return []
        count = len(blob) // 4
        return list(struct.unpack(f"{count}f", blob))

    def _cosine_similarity(self, left: list[float], right: list[float]) -> float:
        if not left or not right or len(left) != len(right): return 0.0
        numerator = sum(a * b for a, b in zip(left, right))
        left_norm = math.sqrt(sum(value * value for value in left))
        right_norm = math.sqrt(sum(value * value for value in right))
        if left_norm == 0 or right_norm == 0: return 0.0
        return numerator / (left_norm * right_norm)

    def _lexical_score(self, query_terms: set[str], text: str) -> float:
        if not query_terms: return 0.0
        lowered = text.lower()
        matches = sum(1 for term in query_terms if term in lowered)
        if not matches: return 0.0
        return matches / max(1, len(query_terms))
