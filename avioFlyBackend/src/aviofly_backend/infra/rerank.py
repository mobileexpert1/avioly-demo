from __future__ import annotations

from ..core.interfaces import Reranker
from ..core.models import RetrievedChunk


class ScoreReranker(Reranker):
    def rerank(self, question: str, chunks: list[RetrievedChunk], limit: int = 5) -> list[RetrievedChunk]:
        ordered = sorted(chunks, key=lambda chunk: chunk.score, reverse=True)
        return ordered[:limit]

