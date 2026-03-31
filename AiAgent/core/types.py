from __future__ import annotations
from dataclasses import dataclass
from typing import Any

@dataclass(frozen=True)
class CollectionContext:
    collection_id: str
    collection_name: str
    language: str = "en"

@dataclass(frozen=True)
class QueryRequest:
    collection_id: str
    question: str
    language: str = "en"

@dataclass(frozen=True)
class RetrievedChunk:
    source_id: str
    document_name: str
    chunk_index: int
    text: str
    score: float = 0.0
    metadata: dict[str, Any] | None = None

@dataclass(frozen=True)
class Answer:
    text: str
    sources: list[RetrievedChunk]
    used_llm: bool
