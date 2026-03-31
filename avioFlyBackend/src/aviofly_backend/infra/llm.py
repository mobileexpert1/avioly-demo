from __future__ import annotations

import os
from dataclasses import dataclass

from ..core.interfaces import ChatService
from ..core.models import ChatRequest, ChatResponse, ChatResponseKind, ChatOption, ChatArtifact, ChatArtifactKind


@dataclass
class ProviderConversationService(ChatService):
    provider_name: str

    def send(self, request: ChatRequest) -> ChatResponse:
        return ChatResponse(
            kind=ChatResponseKind.options if "option" in request.user_message.lower() else ChatResponseKind.text,
            reply="I can help with that.",
            suggested_actions=["Refine request", "Ask another question"],
            options=[
                ChatOption(id="opt-1", title="Option one", value="Show the summary"),
                ChatOption(id="opt-2", title="Option two", value="Give a detailed response"),
            ],
            confidence=0.92,
            artifacts=[
                ChatArtifact(id="sig-1", title="Signal", value="High confidence", kind=ChatArtifactKind.signal)
            ],
            reasoning_summary=f"Response generated via {self.provider_name}.",
            safety_notice="Operational guidance should still be validated by the host system.",
            streaming_supported=True,
            prompt_tokens=120,
            completion_tokens=80,
            latency_ms=240,
        )


def provider_name_from_env() -> str:
    return os.getenv("AVIOFLY_LLM_PROVIDER", "generic-provider")
