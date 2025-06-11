from __future__ import annotations

from ..core.base_agent import BaseAgent


class FallbackAgent(BaseAgent):
    """Default agent if no other agent matches the query."""

    def __init__(self) -> None:
        super().__init__("fallback")

    async def run(self, message: str) -> str:  # noqa: D401 - simple fallback
        return "Please contact Dayne at dayneguy@gmail.com for more information."
