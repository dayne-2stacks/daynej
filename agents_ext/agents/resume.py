from __future__ import annotations

from ..core.base_agent import BaseAgent


class ResumeAgent(BaseAgent):
    """Return a short message representing a rendered resume."""

    def __init__(self) -> None:
        super().__init__("resume")

    async def run(self, message: str) -> str:
        return "Generated resume using renderCV."
