from __future__ import annotations
from dataclasses import dataclass

from ..core.interfaces import Retriever, VectorStore
from ..core.types import QueryRequest, RetrievedChunk

@dataclass
class EmbeddedRetriever(Retriever):
    vector_store: VectorStore
    embedder: object

    def retrieve(self, request: QueryRequest, limit: int = 5) -> list[RetrievedChunk]:
        query_embedding = self.embedder.embed(request.question)
        chunks = self.vector_store.search(request.collection_id, request.question, query_embedding, limit=limit * 8)
        chunks.sort(key=lambda chunk: chunk.score, reverse=True)
        return chunks[:limit]
