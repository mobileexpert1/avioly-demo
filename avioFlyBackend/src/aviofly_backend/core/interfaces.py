from __future__ import annotations

from abc import ABC, abstractmethod

from .models import (
    Budget,
    ChatEnvelope,
    ChatRequest,
    ChatResponse,
    ChatStreamRequest,
    ConversationPage,
    ConversationPageResult,
    RetrievedChunk,
    RetrievalQuery,
    UsageRecord,
)


class ChatService(ABC):
    @abstractmethod
    def send(self, request: ChatRequest) -> ChatResponse: ...


class StreamingChatService(ABC):
    @abstractmethod
    def stream(self, request: ChatStreamRequest):
        raise NotImplementedError


class ConversationRepository(ABC):
    @abstractmethod
    def load_threads(self, page: ConversationPage) -> ConversationPageResult: ...


class RetrievalStore(ABC):
    @abstractmethod
    def search(self, query: RetrievalQuery) -> list[RetrievedChunk]: ...


class VectorStore(ABC):
    @abstractmethod
    def upsert(self, collection_id: str, chunks: list[RetrievedChunk], embeddings: list[list[float]]) -> None: ...

    @abstractmethod
    def search(self, collection_id: str, query_embedding: list[float], limit: int = 5, metadata_filters: dict[str, str] | None = None) -> list[RetrievedChunk]: ...


class EmbeddingProvider(ABC):
    @abstractmethod
    def embed(self, text: str) -> list[float]: ...

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        return [self.embed(t) for t in texts]


class Reranker(ABC):
    @abstractmethod
    def rerank(self, question: str, chunks: list[RetrievedChunk], limit: int = 5) -> list[RetrievedChunk]: ...


class ConnectorPolicy(ABC):
    @abstractmethod
    def is_allowed(self, connector_name: str) -> bool: ...


class UsageTracker(ABC):
    @abstractmethod
    def record(self, usage: UsageRecord) -> None: ...

    @abstractmethod
    def totals_for_conversation(self, conversation_id: str) -> UsageRecord: ...


class BudgetManager(ABC):
    @abstractmethod
    def allow(self, budget: Budget, usage: UsageRecord) -> bool: ...


class Telemetry(ABC):
    @abstractmethod
    def track_event(self, name: str, properties: dict[str, str] | None = None) -> None: ...

    @abstractmethod
    def track_latency(self, name: str, milliseconds: int, properties: dict[str, str] | None = None) -> None: ...


class ConversationCache(ABC):
    @abstractmethod
    def get_threads(self, page: ConversationPage) -> ConversationPageResult | None: ...

    @abstractmethod
    def set_threads(self, page: ConversationPage, result: ConversationPageResult) -> None: ...

    @abstractmethod
    def get_response(self, key: str) -> ChatResponse | None: ...

    @abstractmethod
    def set_response(self, key: str, response: ChatResponse) -> None: ...


class ResponsePolicy(ABC):
    @abstractmethod
    def normalize(self, envelope: ChatEnvelope) -> ChatResponse: ...
