from __future__ import annotations

from ..core.base_agent import BaseAgent


class HobbiesAgent(BaseAgent):
    """Answer questions about hobbies."""

    def __init__(self) -> None:
        super().__init__("hobbies")

    async def run(self, message: str) -> str:
        return (
            "Dayne enjoys exploring hardware design and AI research in his free time."
        )
