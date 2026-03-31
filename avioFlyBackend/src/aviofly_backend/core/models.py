from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class ConversationMode(str, Enum):
    concierge = "concierge"
    support = "support"
    expert = "expert"


class ChatResponseKind(str, Enum):
    text = "text"
    options = "options"
    mixed = "mixed"


class RetrievalSourceType(str, Enum):
    document = "document"
    web = "web"
    connector = "connector"
    profile = "profile"


class ChatArtifactKind(str, Enum):
    recommendation = "recommendation"
    rationale = "rationale"
    signal = "signal"


@dataclass(frozen=True)
class ChatOption:
    id: str
    title: str
    value: str


@dataclass(frozen=True)
class ChatArtifact:
    id: str
    title: str
    value: str
    kind: ChatArtifactKind


@dataclass(frozen=True)
class RetrievedChunk:
    source_id: str
    document_name: str
    chunk_index: int
    text: str
    score: float = 0.0
    metadata: dict[str, Any] | None = None
    source_type: RetrievalSourceType = RetrievalSourceType.document


@dataclass(frozen=True)
class RetrievalQuery:
    collection_id: str
    question: str
    language: str = "en"
    metadata_filters: dict[str, str] = field(default_factory=dict)
    limit: int = 5


@dataclass(frozen=True)
class PassengerProfile:
    loyalty_tier: str | None = None
    travel_preference: str | None = None
    accessibility_needs: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class ChatContext:
    locale_identifier: str
    passenger_profile: PassengerProfile | None = None
    application_context: dict[str, str] = field(default_factory=dict)
    profile_context: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class ConversationPage:
    cursor: str | None
    limit: int


@dataclass(frozen=True)
class ChatRequest:
    request_id: str
    conversation_id: str
    user_message: str
    context: ChatContext
    requested_mode: ConversationMode
    page: ConversationPage
    retrieval_query: RetrievalQuery | None = None


@dataclass(frozen=True)
class ChatStreamRequest:
    request: ChatRequest
    wants_delta_updates: bool = True


@dataclass(frozen=True)
class ChatResponse:
    kind: ChatResponseKind
    reply: str
    suggested_actions: list[str]
    options: list[ChatOption]
    confidence: float
    artifacts: list[ChatArtifact]
    reasoning_summary: str
    safety_notice: str | None = None
    streaming_supported: bool = True
    prompt_tokens: int | None = None
    completion_tokens: int | None = None
    latency_ms: int | None = None


@dataclass(frozen=True)
class ConversationThread:
    id: str
    title: str
    updated_at: str
    preview: str | None = None


@dataclass(frozen=True)
class ConversationPageResult:
    items: list[ConversationThread]
    next_cursor: str | None
    has_more: bool


@dataclass(frozen=True)
class ChatEnvelope:
    response: ChatResponse
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class Budget:
    max_tokens: int | None = None
    max_cost_usd: float | None = None


@dataclass(frozen=True)
class UsageRecord:
    request_id: str
    conversation_id: str
    prompt_tokens: int = 0
    completion_tokens: int = 0
    cost_usd: float = 0.0
    latency_ms: int = 0
    provider: str | None = None
