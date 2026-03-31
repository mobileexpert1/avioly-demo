from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import joblib
from sklearn.feature_extraction.text import TfidfVectorizer

from ...core.interfaces import EmbeddingProvider


@dataclass
class TfidfEmbeddingProvider(EmbeddingProvider):
    model_path: Path
    max_features: int = 20000

    def __post_init__(self) -> None:
        self.model_path.parent.mkdir(parents=True, exist_ok=True)
        self._vectorizer = self._load_or_create()

    def fit(self, texts: list[str]) -> None:
        self._vectorizer = TfidfVectorizer(
            analyzer="word",
            ngram_range=(1, 2),
            lowercase=True,
            stop_words="english",
            max_features=self.max_features,
        )
        self._vectorizer.fit(texts)
        joblib.dump(self._vectorizer, self.model_path)

    def embed(self, text: str) -> list[float]:
        vector = self._vectorizer.transform([text]).toarray()[0]
        return [float(value) for value in vector.tolist()]

    def _load_or_create(self):
        if self.model_path.exists():
            try:
                return joblib.load(self.model_path)
            except Exception:
                pass
        return TfidfVectorizer(
            analyzer="word",
            ngram_range=(1, 2),
            lowercase=True,
            stop_words="english",
            max_features=self.max_features,
        )
