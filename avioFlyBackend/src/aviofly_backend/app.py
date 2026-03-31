from __future__ import annotations

from fastapi import FastAPI

from .core.interfaces import EmbeddingProvider
from .core.models import (
    Budget,
    ChatContext,
    ChatRequest,
    ConversationMode,
    ConversationPage,
    RetrievalQuery,
)
from .core.settings import load_settings
from .domain.cache import InMemoryConversationCache
from .domain.retrieval import RetrievalService
from .domain.policy import DefaultResponsePolicy
from .domain.service import ConversationService
from .domain.usage import InMemoryUsageTracker, SimpleBudgetManager
from .infra.llm import ProviderConversationService, provider_name_from_env
from .infra.rerank import ScoreReranker
from .infra.storage import SQLiteConversationRepository
from .infra.telemetry import ConsoleTelemetry
from .infra.vector_store import InMemoryVectorStore


class HashEmbeddingProvider(EmbeddingProvider):
    def embed(self, text: str) -> list[float]:
        values = [0.0] * 8
        for index, char in enumerate(text.lower()):
            values[index % len(values)] += (ord(char) % 37) / 37.0
        return values


def create_app() -> FastAPI:
    settings = load_settings()
    repository = SQLiteConversationRepository(database_path="var/conversations.sqlite3")
    chat_service = ProviderConversationService(provider_name=provider_name_from_env())
    cache = InMemoryConversationCache(max_entries=settings.cache_size)
    vector_store = InMemoryVectorStore()
    embedder = HashEmbeddingProvider()
    retrieval_service = RetrievalService(
        vector_store=vector_store,
        embedder=embedder,
        reranker=ScoreReranker(),
    )
    usage_tracker = InMemoryUsageTracker()
    telemetry_store = ConsoleTelemetry()
    service = ConversationService(
        repository=repository,
        chat_service=chat_service,
        cache=cache,
        policy=DefaultResponsePolicy(),
        telemetry=telemetry_store,
        usage_tracker=usage_tracker,
        budget_manager=SimpleBudgetManager(),
        retrieval_service=retrieval_service,
        budget=Budget(max_tokens=4096, max_cost_usd=5.0),
        page_size=settings.page_size,
    )

    app = FastAPI(title=settings.app_name)

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/conversations")
    def list_conversations(cursor: str | None = None) -> dict:
        page = service.load_threads(cursor=cursor)
        return {
            "items": [thread.__dict__ for thread in page.items],
            "next_cursor": page.next_cursor,
            "has_more": page.has_more,
        }

    @app.post("/chat")
    def chat(payload: dict) -> dict:
        request = ChatRequest(
            request_id=payload["request_id"],
            conversation_id=payload["conversation_id"],
            user_message=payload["user_message"],
            context=ChatContext(
                locale_identifier=payload.get("locale_identifier", settings.default_locale),
                passenger_profile=None,
                application_context=payload.get("application_context", {}),
                profile_context=payload.get("profile_context", {}),
            ),
            requested_mode=ConversationMode(payload.get("requested_mode", "concierge")),
            page=ConversationPage(cursor=payload.get("cursor"), limit=int(payload.get("limit", settings.page_size))),
            retrieval_query=RetrievalQuery(
                collection_id=payload.get("collection_id", "default"),
                question=payload["user_message"],
                language=payload.get("locale_identifier", settings.default_locale),
                metadata_filters=payload.get("metadata_filters", {}),
                limit=int(payload.get("retrieval_limit", 5)),
            )
            if payload.get("collection_id")
            else None,
        )
        response = service.send(request)
        return {
            "kind": response.kind.value,
            "reply": response.reply,
            "suggested_actions": response.suggested_actions,
            "options": [option.__dict__ for option in response.options],
            "confidence": response.confidence,
            "artifacts": [artifact.__dict__ for artifact in response.artifacts],
            "reasoning_summary": response.reasoning_summary,
            "safety_notice": response.safety_notice,
            "streaming_supported": response.streaming_supported,
            "prompt_tokens": response.prompt_tokens,
            "completion_tokens": response.completion_tokens,
            "latency_ms": response.latency_ms,
        }

    @app.get("/usage/{conversation_id}")
    def usage(conversation_id: str) -> dict:
        record = usage_tracker.totals_for_conversation(conversation_id)
        return {
            "request_id": record.request_id,
            "conversation_id": record.conversation_id,
            "prompt_tokens": record.prompt_tokens,
            "completion_tokens": record.completion_tokens,
            "cost_usd": record.cost_usd,
            "latency_ms": record.latency_ms,
            "provider": record.provider,
        }

    @app.get("/telemetry")
    def telemetry() -> dict:
        return {
            "events": telemetry_store.events,
            "latencies": telemetry_store.latencies,
        }

    return app
