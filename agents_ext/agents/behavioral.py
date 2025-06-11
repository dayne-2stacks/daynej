from __future__ import annotations

import os
from openai import OpenAI

from ..core.retrieval_agent import RetrievalAgent
from .utils import load_json


class BehavioralQuestionAgent(RetrievalAgent):
    """Answer interview style questions using Dayne's past experiences."""

    def __init__(
        self,
        model: str = "gpt-4o",
        embed_model: str = "text-embedding-3-small",
        rerank_models: list[str] | None = ["BAAI/bge-reranker-v2-m3"],
    ) -> None:
        self.experiences = load_json("experiences.json")
        super().__init__(
            "behavioral",
            data=self.experiences,
            model=model,
            embed_model=embed_model,
            rerank_models=rerank_models,
        )
        self.client = OpenAI(api_key=os.getenv("JOB_API"))

    def _get_entry_text(self, entry: dict) -> str:  # type: ignore[override]
        return entry.get("answer") or entry.get("question", "")

    def _top_experiences(self, query: str, k: int = 3) -> list[str]:
        entries = self.retrieve(query, k)
        print(f"Top {k} experiences for query: {query}")
        if not entries:
            return ["No relevant experiences found."]
        else:
            print(f"Found {len(entries)} relevant experiences.")
            print("Top experiences:")
        for e in entries:
            print(f"- {self._get_entry_text(e)}")
        return [self._get_entry_text(e) for e in entries]

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
    from dotenv import load_dotenv

    load_dotenv()

    parser = argparse.ArgumentParser(
        description="Answer a behavioral interview question. Respoond using the STAR method (Situation, Task, Action, Result)."
    )
    parser.add_argument("question", nargs="?", help="Question to ask")
    args = parser.parse_args()

    question = args.question or input("Question: ")

    agent = BehavioralQuestionAgent()
    reply = asyncio.run(agent.run(question))
    print(reply)
