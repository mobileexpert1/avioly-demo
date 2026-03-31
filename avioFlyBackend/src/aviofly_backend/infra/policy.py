from __future__ import annotations

from ..core.errors import InvalidResponseError
from ..core.interfaces import ResponsePolicy
from ..core.models import ChatEnvelope, ChatResponse


class StrictResponsePolicy(ResponsePolicy):
    def normalize(self, envelope: ChatEnvelope) -> ChatResponse:
        response = envelope.response
        if not response.reply.strip():
            raise InvalidResponseError("assistant reply is empty")
        if response.confidence < 0:
            raise InvalidResponseError("confidence must not be negative")
        return response

