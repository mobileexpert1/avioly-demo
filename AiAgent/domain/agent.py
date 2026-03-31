from __future__ import annotations
from dataclasses import dataclass
from ..core.interfaces import Agent, EmbeddingProvider, LLMProvider, Retriever
from ..core.types import Answer, QueryRequest
import os

@dataclass
class GenericAssistantAgent(Agent):
    retriever: Retriever
    embedder: EmbeddingProvider
    llm: LLMProvider | None = None

    def answer(self, request: QueryRequest) -> Answer:
        chunks = self.retriever.retrieve(request, limit=15)
        if not chunks:
            return Answer(
                text="I could not find relevant information in the documents.",
                sources=[],
                used_llm=False,
            )

        if self.llm is None:
            # Fallback if no Gemini is configured
            return Answer(
                text="[WARNING: Gemini API Key missing. Showing top retrieved text:]\n\n" + chunks[0].text,
                sources=chunks,
                used_llm=False,
            )

        prompt = self._build_prompt(request.question, chunks)
        text = self.llm.generate(prompt).strip()
        if not text:
            return Answer(
                text="[WARNING: Gemini model failed. Showing top retrieved text:]\n\n" + chunks[0].text,
                sources=chunks,
                used_llm=False,
            )
        return Answer(text=text, sources=chunks, used_llm=True)

    def _build_prompt(self, question: str, chunks) -> str:
        org_name = os.getenv("ORGANIZATION_NAME", "your organization")
        context = "\n\n".join(
            f"[{chunk.document_name} page {chunk.metadata.get('page_number') if chunk.metadata else '?'}] {chunk.text}"
            for chunk in chunks
        )
        return (
            f"You are a helpful assistant for {org_name}.\n"
            "Use the provided Source Context to answer the user's question accurately.\n"
            "Rules:\n"
            "- Keep your answer clear and concise.\n"
            "- Base your answer ONLY on the facts in the Source Context.\n"
            "- If the Source Context does not contain the answer, say you do not know.\n"
            "- If the answer is a list, format it with bullets.\n\n"
            f"Question: {question}\n\n"
            f"Source Context:\n{context}"
        )
