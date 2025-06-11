from __future__ import annotations

import json
from pathlib import Path

from ..core.base_agent import BaseAgent

DATA_DIR = Path(__file__).resolve().parents[2] / "api" / "kb"


def _load_json(file_name: str) -> dict:
    with open(DATA_DIR / file_name, "r") as f:
        return json.load(f)


class PersonalInfoAgent(BaseAgent):
    """Provide contact and location information about Dayne."""

    def __init__(self) -> None:
        super().__init__("personal-info")
        self.data = _load_json("dayne.json")

    async def run(self, message: str) -> str:
        text = message.lower()
        info = self.data["PersonalInformation"]
        if "contact" in text or "email" in text:
            return info["Contact"]
        if "location" in text or "where" in text:
            return info["Location"]
        return info["Name"]


class ExperienceAgent(BaseAgent):
    """Return a brief description of Dayne's projects."""

    def __init__(self) -> None:
        super().__init__("experience")
        self.data = _load_json("dayne.json")

    async def run(self, message: str) -> str:
        projects = self.data.get("Projects", [])
        if projects:
            first = projects[0]
            return f"Example project: {first['Title']}"
        return "No project information available."


class HobbiesAgent(BaseAgent):
    """Answer questions about hobbies."""

    def __init__(self) -> None:
        super().__init__("hobbies")

    async def run(self, message: str) -> str:
        return (
            "Dayne enjoys exploring hardware design and AI research in his free time."
        )


class FallbackAgent(BaseAgent):
    """Default agent if no other agent matches the query."""

    def __init__(self) -> None:
        super().__init__("fallback")

    async def run(self, message: str) -> str:  # noqa: D401 - simple fallback
        return "Please contact Dayne at dayneguy@gmail.com for more information."


class TriageAgent(BaseAgent):
    """Route messages to specialized agents based on simple keywords."""

    def __init__(self) -> None:
        super().__init__("triage")
        self.personal = PersonalInfoAgent()
        self.experience = ExperienceAgent()
        self.hobbies = HobbiesAgent()
        self.fallback = FallbackAgent()

    async def run(self, message: str) -> str:
        text = message.lower()
        if any(k in text for k in ["contact", "email", "location"]):
            return await self.personal.run(message)
        if any(k in text for k in ["intern", "project", "experience"]):
            return await self.experience.run(message)
        if "hobby" in text or "hobbies" in text:
            return await self.hobbies.run(message)
        return await self.fallback.run(message)
