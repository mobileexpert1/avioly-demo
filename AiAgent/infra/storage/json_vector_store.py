from __future__ import annotations
import json
from dataclasses import asdict
from pathlib import Path

from ...core.interfaces import DocumentStore, VectorStore
from ...core.types import RetrievedChunk

class JsonVectorStore(DocumentStore, VectorStore):
    def __init__(self, path: Path):
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if not self.path.exists():
            self.path.write_text("{}", encoding="utf-8")

    def save_chunks(self, collection_id: str, chunks: list[RetrievedChunk]) -> None:
        self.upsert(collection_id, chunks, []) # Fallback behaviour

    def list_documents(self, collection_id: str) -> list[str]:
        data = json.loads(self.path.read_text(encoding="utf-8"))
        items = data.get(collection_id, [])
        return sorted({item["document_name"] for item in items})

    def upsert(self, collection_id: str, chunks: list[RetrievedChunk], embeddings: list[list[float]]) -> None:
        data = json.loads(self.path.read_text(encoding="utf-8"))
        data[collection_id] = [
            {**asdict(chunk), "embedding": embedding}
            for chunk, embedding in zip(chunks, embeddings, strict=True)
        ]
        self.path.write_text(json.dumps(data, indent=2, sort_keys=True), encoding="utf-8")

    def search(self, collection_id: str, query: str, query_embedding: list[float], limit: int = 5) -> list[RetrievedChunk]:
        data = json.loads(self.path.read_text(encoding="utf-8"))
        items = data.get(collection_id, [])
        scored: list[tuple[float, dict]] = []
        for item in items:
            stored = item.get("embedding", [])
            score = self._cosine_similarity(query_embedding, stored)
            scored.append((score, item))
        scored.sort(key=lambda pair: pair[0], reverse=True)
        return [
            RetrievedChunk(
                source_id=collection_id,
                document_name=item["document_name"],
                chunk_index=item["chunk_index"],
                text=item["text"],
                score=score,
                metadata=item.get("metadata"),
            )
            for score, item in scored[:limit]
        ]

    def _cosine_similarity(self, left: list[float], right: list[float]) -> float:
        if not left or not right or len(left) != len(right):
            return 0.0
        numerator = sum(a * b for a, b in zip(left, right))
        left_norm = sum(value * value for value in left) ** 0.5
        right_norm = sum(value * value for value in right) ** 0.5
        if left_norm == 0 or right_norm == 0:
            return 0.0
        return numerator / (left_norm * right_norm)
