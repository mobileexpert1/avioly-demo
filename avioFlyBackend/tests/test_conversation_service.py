from aviofly_backend.core.models import (
    Budget,
    ChatContext,
    ChatRequest,
    ConversationMode,
    ConversationPage,
    RetrievalQuery,
    RetrievedChunk,
    RetrievalSourceType,
    UsageRecord,
)
from aviofly_backend.domain.cache import InMemoryConversationCache
from aviofly_backend.domain.policy import DefaultResponsePolicy
from aviofly_backend.domain.service import ConversationService
from aviofly_backend.domain.retrieval import RetrievalService
from aviofly_backend.domain.usage import InMemoryUsageTracker, SimpleBudgetManager
from aviofly_backend.infra.llm import ProviderConversationService
from aviofly_backend.infra.rerank import ScoreReranker
from aviofly_backend.infra.vector_store import InMemoryVectorStore


def test_chat_service_returns_options_when_requested():
    service = ProviderConversationService(provider_name="test-provider")
    response = service.send(
        ChatRequest(
            request_id="r1",
            conversation_id="c1",
            user_message="Give me options",
            context=ChatContext(locale_identifier="en", application_context={}),
            requested_mode=ConversationMode.support,
            page=ConversationPage(cursor=None, limit=20),
            retrieval_query=None,
        )
    )
    assert response.kind.value == "options"
    assert len(response.options) == 2
    assert response.prompt_tokens == 120


def test_conversation_service_uses_cache():
    class Repo:
        def __init__(self):
            self.calls = 0

        def load_threads(self, page):
            self.calls += 1
            return type(
                "PageResult",
                (),
                {"items": [], "next_cursor": None, "has_more": False},
            )()

    class Chat:
        def send(self, request):
            return ProviderConversationService(provider_name="test").send(request)

    repo = Repo()
    cache = InMemoryConversationCache()
    vector_store = InMemoryVectorStore()
    vector_store.upsert(
        "default",
        [
            RetrievedChunk(
                source_id="doc1",
                document_name="Policies",
                chunk_index=0,
                text="Policy text",
                score=0.9,
                source_type=RetrievalSourceType.document,
            )
        ],
        [[0.1] * 8],
    )
    service = ConversationService(
        repo,
        Chat(),
        cache,
        DefaultResponsePolicy(),
        usage_tracker=InMemoryUsageTracker(),
        budget_manager=SimpleBudgetManager(),
        retrieval_service=RetrievalService(vector_store=vector_store, embedder=type("E", (), {"embed": lambda self, text: [0.1] * 8})()),
        budget=Budget(max_tokens=4096, max_cost_usd=10.0),
    )

    page = service.load_threads()
    assert page.has_more is False
    assert repo.calls == 1
    page2 = service.load_threads()
    assert repo.calls == 1


def test_retrieval_service_filters_and_reranks():
    vector_store = InMemoryVectorStore()
    vector_store.upsert(
        "docs",
        [
            RetrievedChunk("a", "Doc A", 0, "Alpha", 0.2, {"category": "finance"}),
            RetrievedChunk("b", "Doc B", 1, "Beta", 0.9, {"category": "finance"}),
            RetrievedChunk("c", "Doc C", 2, "Gamma", 0.5, {"category": "ops"}),
        ],
        [[0.1] * 8, [0.2] * 8, [0.3] * 8],
    )

    class Emb:
        def embed(self, text):
            return [0.2] * 8

    service = RetrievalService(vector_store=vector_store, embedder=Emb(), reranker=ScoreReranker(), max_context_chunks=2)
    results = service.search(RetrievalQuery(collection_id="docs", question="finance", metadata_filters={"category": "finance"}, limit=2))
    assert len(results) == 2
    assert results[0].score >= results[1].score


def test_budget_manager_blocks_overages():
    manager = SimpleBudgetManager()
    assert manager.allow(Budget(max_tokens=100, max_cost_usd=1.0), UsageRecord(request_id="r", conversation_id="c", prompt_tokens=30, completion_tokens=20, cost_usd=0.5))
    assert not manager.allow(Budget(max_tokens=10, max_cost_usd=1.0), UsageRecord(request_id="r", conversation_id="c", prompt_tokens=30, completion_tokens=20, cost_usd=0.5))
