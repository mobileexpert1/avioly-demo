from __future__ import annotations

from dataclasses import dataclass

from ...core.interfaces import LLMProvider


@dataclass
class GeminiProvider(LLMProvider):
    api_key: str
    model_name: str

    def __post_init__(self) -> None:
        from google import genai

        self._client = genai.Client(api_key=self.api_key)

    def generate(self, prompt: str) -> str:
        try:
            response = self._client.models.generate_content(
                model=self.model_name,
                contents=prompt,
            )
            return getattr(response, "text", "") or ""
        except Exception as e:
            import logging
            logging.error(f"Gemini generation failed: {e}")
            return ""


class NullLLMProvider(LLMProvider):
    def generate(self, prompt: str) -> str:
        return ""
