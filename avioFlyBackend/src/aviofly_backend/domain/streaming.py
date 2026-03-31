from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from ..core.models import ChatStreamRequest, ChatResponse


@dataclass(frozen=True)
class StreamDelta:
    text: str | None = None
    response: ChatResponse | None = None
    finished: bool = False


class ConversationStreamer:
    def stream(self, request: ChatStreamRequest) -> Iterable[StreamDelta]:
        raise NotImplementedError

