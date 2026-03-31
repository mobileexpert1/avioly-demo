from __future__ import annotations

from dataclasses import dataclass, field

from ..core.interfaces import VectorStore
from ..core.models import RetrievedChunk


@dataclass
class InMemoryVectorStore(VectorStore):
    chunks: dict[str, list[RetrievedChunk]] = field(default_factory=dict)

    def upsert(self, collection_id: str, chunks: list[RetrievedChunk], embeddings: list[list[float]]) -> None:
        existing = self.chunks.get(collection_id, [])
        self.chunks[collection_id] = existing + chunks

    def search(
        self,
        collection_id: str,
        query_embedding: list[float],
        limit: int = 5,
        metadata_filters: dict[str, str] | None = None,
    ) -> list[RetrievedChunk]:
        candidates = self.chunks.get(collection_id, [])
        if metadata_filters:
            candidates = [
                chunk for chunk in candidates
                if all(str((chunk.metadata or {}).get(key)) == value for key, value in metadata_filters.items())
            ]
        return sorted(candidates, key=lambda chunk: chunk.score, reverse=True)[:limit]

