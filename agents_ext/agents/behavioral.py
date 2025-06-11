from __future__ import annotations

import os
from math import sqrt

from openai import OpenAI

from ..core.base_agent import BaseAgent
from .utils import load_json


class BehavioralQuestionAgent(BaseAgent):
    """Answer interview style questions using Dayne's past experiences."""

    def __init__(
        self, model: str = "gpt-4o", embed_model: str = "text-embedding-3-small"
    ) -> None:
        super().__init__("behavioral")
        self.client = OpenAI(api_key=os.getenv("JOB_API"))
        self.model = model
        self.embed_model = embed_model
        self.experiences = load_json("experiences.json")
        self._embeddings: list[list[float]] | None = None

    def _embed(self, text: str) -> list[float]:
        response = self.client.embeddings.create(model=self.embed_model, input=text)
        return response.data[0].embedding

    def _ensure_embeddings(self) -> None:
        if self._embeddings is not None:
            return
        self._embeddings = []
        for entry in self.experiences:
            text = entry.get("answer") or entry.get("question", "")
            self._embeddings.append(self._embed(text))

    @staticmethod
    def _cosine(a: list[float], b: list[float]) -> float:
        dot = sum(x * y for x, y in zip(a, b))
        norm_a = sqrt(sum(x * x for x in a))
        norm_b = sqrt(sum(x * x for x in b))
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return dot / (norm_a * norm_b)

    def _top_experiences(self, query: str, k: int = 3) -> list[str]:
        self._ensure_embeddings()
        query_emb = self._embed(query)
        scores = [self._cosine(query_emb, emb) for emb in self._embeddings or []]
        ranked = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)
        result = []
        for idx in ranked[:k]:
            text = self.experiences[idx].get("answer")
            if text:
                result.append(text)
        return result

    def _build_messages(self, question: str) -> list[dict]:
        history = self.memory.messages[-5:]
        context = "\n".join(self._top_experiences(question))
        messages = [
            {
                "role": "system",
                "content": "Answer the user's behavioral question only using the experiences provided.",
            },
            {"role": "system", "content": f"Relevant experiences:\n{context}"},
        ]
        messages.extend(history)
        messages.append({"role": "user", "content": question})
        return messages

    async def run(self, message: str) -> str:
        self.add_message("user", message)
        messages = self._build_messages(message)
        response = self.client.chat.completions.create(
            model=self.model, messages=messages
        )
        content = response.choices[0].message.content.strip()
        self.add_message("assistant", content)
        return content


if __name__ == "__main__":
    import argparse
    import asyncio

    parser = argparse.ArgumentParser(
        description="Answer a behavioral interview question"
    )
    parser.add_argument("question", nargs="?", help="Question to ask")
    args = parser.parse_args()

    question = args.question or input("Question: ")

    agent = BehavioralQuestionAgent()
    reply = asyncio.run(agent.run(question))
    print(reply)
