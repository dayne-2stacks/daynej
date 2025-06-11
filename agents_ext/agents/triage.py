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


class BehavioralQuestionAgent(BaseAgent):
    """Handle typical interview or behavioral questions."""

    def __init__(self) -> None:
        super().__init__("behavioral")
        self.qa_pairs = _load_json("behavioral_questions.json")

    async def run(self, message: str) -> str:
        text = message.lower()
        for pair in self.qa_pairs:
            if pair["question"].lower() in text:
                return pair.get("answer") or "Dayne is still preparing an answer."
        return "Dayne reflects on past experiences to answer that question."


class ResumeAgent(BaseAgent):
    """Return a short message representing a rendered resume."""

    def __init__(self) -> None:
        super().__init__("resume")

    async def run(self, message: str) -> str:
        return "Generated resume using renderCV."


class CalendarAgent(BaseAgent):
    """Simulate creating a calendar event."""

    def __init__(self) -> None:
        super().__init__("calendar")

    async def run(self, message: str) -> str:
        return "Scheduled a meeting with Dayne."


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
        self.behavioral = BehavioralQuestionAgent()
        self.resume = ResumeAgent()
        self.calendar = CalendarAgent()
        self.fallback = FallbackAgent()

    async def run(self, message: str) -> str:
        text = message.lower()
        if any(k in text for k in ["contact", "email", "location"]):
            return await self.personal.run(message)
        if any(k in text for k in ["intern", "project", "experience"]):
            return await self.experience.run(message)
        if "hobby" in text or "hobbies" in text:
            return await self.hobbies.run(message)
        if "behavioral" in text or "interview" in text:
            return await self.behavioral.run(message)
        if "resume" in text or "cv" in text:
            return await self.resume.run(message)
        if "meeting" in text or "calendar" in text:
            return await self.calendar.run(message)
        return await self.fallback.run(message)
