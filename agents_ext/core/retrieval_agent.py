from __future__ import annotations

import os
from math import sqrt
from typing import Any, Dict, List

os.environ["HF_HOME"] = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "models"))

try:
    from sentence_transformers.cross_encoder import CrossEncoder  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    print("sentence-transformers not installed; reranking will be unavailable.")
    CrossEncoder = None

from openai import OpenAI

from .base_agent import BaseAgent



class RetrievalAgent(BaseAgent):
    """Base agent providing embedding based retrieval with optional reranking."""

    def __init__(
        self,
        name: str,
        data: List[Dict[str, Any]],
        model: str = "gpt-4o",
        embed_model: str = "text-embedding-3-small",
        rerank_models: List[str] | None = None,
    ) -> None:
        super().__init__(name)
        
        self.client = OpenAI(api_key=os.getenv("JOB_API"))
        self.model = model
        self.embed_model = embed_model
        self.rerank_models = rerank_models or [
            "BAAI/bge-reranker-v2-m3",
        ]
        self._rerankers: Dict[str, Any] = {}
        self.data = data
        self._embeddings: List[List[float]] | None = None

    def _get_entry_text(self, entry: Dict[str, Any]) -> str:
        """Return text used for embeddings. Subclasses may override."""
        return str(entry)

    def _embed(self, text: str, model: str | None = None) -> List[float]:
        model = model or self.embed_model
        response = self.client.embeddings.create(model=model, input=text)
        return response.data[0].embedding

    def _ensure_embeddings(self) -> None:
        if self._embeddings is not None:
            return
        self._embeddings = [self._embed(self._get_entry_text(e)) for e in self.data]

    def _get_reranker(self, model: str):
        if CrossEncoder is None:
            raise RuntimeError(
                "sentence-transformers not installed; reranking unavailable"
            )
        if model not in self._rerankers:
            self._rerankers[model] = CrossEncoder(model)
        print(f"Using reranker model: {model}")
        return self._rerankers[model]

    @staticmethod
    def _cosine(a: List[float], b: List[float]) -> float:
        dot = sum(x * y for x, y in zip(a, b))
        norm_a = sqrt(sum(x * x for x in a))
        norm_b = sqrt(sum(x * x for x in b))
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return dot / (norm_a * norm_b)

    def retrieve(self, query: str, k: int = 3) -> List[Dict[str, Any]]:
        """Retrieve top-k entries using embeddings and rerank them."""
        self._ensure_embeddings()
        query_emb = self._embed(query)
        scores = [self._cosine(query_emb, emb) for emb in self._embeddings or []]
        ranked = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)
        candidates = [self.data[i] for i in ranked[:k]]
        return self._rerank(query, candidates)

    def _rerank(
        self, query: str, candidates: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        if not self.rerank_models or not candidates:
            print("No reranking models configured or no candidates found.")
            return candidates
        if CrossEncoder is None:
            print("Reranking not available; CrossEncoder not installed.")
            return candidates

        results = candidates
        for model in self.rerank_models:
            try:
                reranker = self._get_reranker(model)
            except RuntimeError:
                break
            pairs = [[query, self._get_entry_text(c)] for c in results]
            scores = reranker.predict(pairs)
            ranked = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)
            results = [results[i] for i in ranked]
        return results
