from __future__ import annotations

from .memory import Memory
from .planner import Planner


class BaseAgent:
    """Base class providing memory and simple echo capability."""

    def __init__(
        self, name: str, memory: Memory | None = None, planner: Planner | None = None
    ) -> None:
        self.name = name
        self.memory = memory or Memory()
        self.planner = planner or Planner()

    def add_message(self, role: str, content: str) -> None:
        self.memory.add(role, content)

    def get_last_message(self) -> str | None:
        last = self.memory.last()
        return last["content"] if last else None

    async def run(self, message: str) -> str:
        """Echo back the message for now."""
        self.add_message("user", message)
        response = f"{self.name} received: {message}"
        self.add_message("assistant", response)
        return response
