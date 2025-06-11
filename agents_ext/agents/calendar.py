from __future__ import annotations

from ..core.base_agent import BaseAgent


class CalendarAgent(BaseAgent):
    """Simulate creating a calendar event."""

    def __init__(self) -> None:
        super().__init__("calendar")

    async def run(self, message: str) -> str:
        return "Scheduled a meeting with Dayne."
