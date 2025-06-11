from __future__ import annotations

from ..core.base_agent import BaseAgent
from .utils import load_json


class ExperienceAgent(BaseAgent):
    """Return a brief description of Dayne's projects."""

    def __init__(self) -> None:
        super().__init__("experience")
        self.data = load_json("dayne.json")

    async def run(self, message: str) -> str:
        projects = self.data.get("Projects", [])
        if projects:
            first = projects[0]
            return f"Example project: {first['Title']}"
        return "No project information available."
