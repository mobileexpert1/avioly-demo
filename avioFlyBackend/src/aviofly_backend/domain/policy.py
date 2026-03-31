from __future__ import annotations

from ..core.interfaces import ResponsePolicy
from ..core.models import ChatEnvelope, ChatResponse


class DefaultResponsePolicy(ResponsePolicy):
    def normalize(self, envelope: ChatEnvelope) -> ChatResponse:
        response = envelope.response
        if not response.reply.strip():
            raise ValueError("empty assistant reply")
        return response

