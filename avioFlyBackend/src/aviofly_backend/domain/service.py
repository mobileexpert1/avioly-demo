from __future__ import annotations

from dataclasses import dataclass

from ..core.interfaces import (
    BudgetManager,
    ChatService,
    ConversationCache,
    ConversationRepository,
    ResponsePolicy,
    Telemetry,
    UsageTracker,
)
from ..core.models import (
    Budget,
    ChatEnvelope,
    ChatRequest,
    ChatResponse,
    ConversationPage,
    ConversationPageResult,
    UsageRecord,
)
from .retrieval import RetrievalService


@dataclass
class ConversationService:
    repository: ConversationRepository
    chat_service: ChatService
    cache: ConversationCache
    policy: ResponsePolicy
    telemetry: Telemetry | None = None
    usage_tracker: UsageTracker | None = None
    budget_manager: BudgetManager | None = None
    retrieval_service: RetrievalService | None = None
    budget: Budget | None = None
    page_size: int = 20

    def load_threads(self, cursor: str | None = None) -> ConversationPageResult:
        page = ConversationPage(cursor=cursor, limit=self.page_size)
        cached = self.cache.get_threads(page)
        if cached is not None:
            if self.telemetry:
                self.telemetry.track_event("threads_cache_hit", {"cursor": cursor or "root"})
            return cached
        result = self.repository.load_threads(page)
        self.cache.set_threads(page, result)
        if self.telemetry:
            self.telemetry.track_event("threads_cache_miss", {"cursor": cursor or "root"})
        return result

    def send(self, request: ChatRequest) -> ChatResponse:
        cache_key = self._response_cache_key(request)
        cached = self.cache.get_response(cache_key)
        if cached is not None:
            if self.telemetry:
                self.telemetry.track_event("chat_cache_hit", {"conversation_id": request.conversation_id})
            return cached

        if self.telemetry:
            self.telemetry.track_event("chat_started", {"conversation_id": request.conversation_id})

        retrieval_chunks = []
        if self.retrieval_service and request.retrieval_query is not None:
            # Retrieval stays separate from generation so the host can swap search backends independently.
            retrieval_chunks = self.retrieval_service.search(request.retrieval_query)
            if self.telemetry:
                self.telemetry.track_event("retrieval_completed", {"count": str(len(retrieval_chunks))})

        response = self.chat_service.send(request)
        normalized = self.policy.normalize(ChatEnvelope(response=response))
        if self.usage_tracker:
            # Usage is recorded after normalization so the tracked response matches what the caller sees.
            usage = UsageRecord(
                request_id=request.request_id,
                conversation_id=request.conversation_id,
                prompt_tokens=normalized.prompt_tokens or 0,
                completion_tokens=normalized.completion_tokens or 0,
                latency_ms=normalized.latency_ms or 0,
                provider=normalized.reasoning_summary or None,
            )
            if self.budget_manager and self.budget and not self.budget_manager.allow(self.budget, usage):
                raise ValueError("budget exceeded")
            self.usage_tracker.record(usage)
        if self.telemetry:
            self.telemetry.track_latency(
                "chat_latency",
                normalized.latency_ms or 0,
                {"conversation_id": request.conversation_id, "retrieval_chunks": str(len(retrieval_chunks))},
            )
        self.cache.set_response(cache_key, normalized)
        return normalized

    def _response_cache_key(self, request: ChatRequest) -> str:
        return "::".join(
            [
                request.requested_mode.value,
                request.user_message.strip().lower(),
                request.page.cursor or "root",
                str(request.page.limit),
            ]
        )
