from __future__ import annotations

from ..core.base_agent import BaseAgent


class AgentRunner:
    """Execute an agent on a message."""

    def __init__(self, agent: BaseAgent) -> None:
        self.agent = agent

    async def run(self, message: str) -> str:
        return await self.agent.run(message)
