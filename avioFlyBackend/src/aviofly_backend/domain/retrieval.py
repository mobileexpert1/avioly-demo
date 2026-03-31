from __future__ import annotations

from dataclasses import dataclass

from ..core.interfaces import EmbeddingProvider, Reranker, RetrievalStore, VectorStore
from ..core.models import RetrievedChunk, RetrievalQuery


@dataclass
class RetrievalService(RetrievalStore):
    vector_store: VectorStore
    embedder: EmbeddingProvider
    reranker: Reranker | None = None
    max_context_chunks: int = 5

    def search(self, query: RetrievalQuery) -> list[RetrievedChunk]:
        # Pull a broader set first, then narrow it down with ranking and filtering.
        query_embedding = self.embedder.embed(query.question)
        chunks = self.vector_store.search(
            query.collection_id,
            query_embedding,
            limit=max(query.limit * 4, self.max_context_chunks),
            metadata_filters=query.metadata_filters,
        )
        ranked = self.reranker.rerank(query.question, chunks, limit=query.limit) if self.reranker else chunks
        return ranked[: query.limit]
