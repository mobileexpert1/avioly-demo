from __future__ import annotations

import os
os.environ["USE_TF"] = "NO"
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"

import logging
from dataclasses import dataclass
from pathlib import Path

from sentence_transformers import SentenceTransformer

from ...core.interfaces import EmbeddingProvider

logger = logging.getLogger(__name__)

@dataclass
class SentenceTransformerEmbeddingProvider(EmbeddingProvider):
    model_name: str = "sentence-transformers/all-MiniLM-L6-v2"
    _model: SentenceTransformer | None = None

    def __post_init__(self) -> None:
        self._load_model()

    def _load_model(self) -> None:
        if self._model is None:
            logger.info(f"Loading SentenceTransformer model: {self.model_name}")
            self._model = SentenceTransformer(self.model_name)

    def fit(self, texts: list[str]) -> None:
        # Pre-trained dense models do not require fitting on the corpus
        pass

    def embed(self, text: str) -> list[float]:
        self._load_model()
        vector = self._model.encode(text)
        return [float(value) for value in vector]

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        self._load_model()
        vectors = self._model.encode(texts, show_progress_bar=True)
        return [[float(v) for v in vector] for vector in vectors]
