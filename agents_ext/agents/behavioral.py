from __future__ import annotations

from ..core.base_agent import BaseAgent
from .utils import load_json


class BehavioralQuestionAgent(BaseAgent):
    """Handle typical interview or behavioral questions."""

    def __init__(self) -> None:
        super().__init__("behavioral")
        self.qa_pairs = load_json("behavioral_questions.json")

    async def run(self, message: str) -> str:
        text = message.lower()
        for pair in self.qa_pairs:
            if pair["question"].lower() in text:
                return pair.get("answer") or "Dayne is still preparing an answer."
        return "Dayne reflects on past experiences to answer that question."
