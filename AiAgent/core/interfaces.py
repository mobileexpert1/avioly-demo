from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Protocol
from .types import Answer, QueryRequest, RetrievedChunk, CollectionContext

class LLMProvider(ABC):
    @abstractmethod
    def generate(self, prompt: str) -> str: ...

class EmbeddingProvider(ABC):
    @abstractmethod
    def embed(self, text: str) -> list[float]: ...
    
    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        return [self.embed(t) for t in texts]

class DocumentStore(ABC):
    @abstractmethod
    def save_chunks(self, collection_id: str, chunks: list[RetrievedChunk]) -> None: ...

    @abstractmethod
    def list_documents(self, collection_id: str) -> list[str]: ...

class VectorStore(ABC):
    @abstractmethod
    def upsert(self, collection_id: str, chunks: list[RetrievedChunk], embeddings: list[list[float]]) -> None: ...

    @abstractmethod
    def search(self, collection_id: str, query: str, query_embedding: list[float], limit: int = 5) -> list[RetrievedChunk]: ...

class ConfigStore(ABC):
    @abstractmethod
    def get(self, collection_id: str) -> CollectionContext: ...

    @abstractmethod
    def upsert(self, config: CollectionContext) -> None: ...

class Retriever(ABC):
    @abstractmethod
    def retrieve(self, request: QueryRequest, limit: int = 5) -> list[RetrievedChunk]: ...

class Agent(ABC):
    @abstractmethod
    def answer(self, request: QueryRequest) -> Answer: ...
