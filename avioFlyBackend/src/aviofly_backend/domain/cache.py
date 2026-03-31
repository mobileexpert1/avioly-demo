from __future__ import annotations

from collections import OrderedDict

from ..core.interfaces import ConversationCache
from ..core.models import ChatResponse, ConversationPage, ConversationPageResult


class InMemoryConversationCache(ConversationCache):
    def __init__(self, max_entries: int = 50) -> None:
        self._max_entries = max_entries
        self._threads: OrderedDict[str, ConversationPageResult] = OrderedDict()
        self._responses: OrderedDict[str, ChatResponse] = OrderedDict()

    def get_threads(self, page: ConversationPage) -> ConversationPageResult | None:
        return self._threads.get(self._key(page))

    def set_threads(self, page: ConversationPage, result: ConversationPageResult) -> None:
        key = self._key(page)
        self._threads[key] = result
        self._threads.move_to_end(key)
        self._trim(self._threads)

    def get_response(self, key: str) -> ChatResponse | None:
        return self._responses.get(key)

    def set_response(self, key: str, response: ChatResponse) -> None:
        self._responses[key] = response
        self._responses.move_to_end(key)
        self._trim(self._responses)

    def _key(self, page: ConversationPage) -> str:
        return f"{page.cursor or 'root'}::{page.limit}"

    def _trim(self, store: OrderedDict[str, object]) -> None:
        while len(store) > self._max_entries:
            store.popitem(last=False)

