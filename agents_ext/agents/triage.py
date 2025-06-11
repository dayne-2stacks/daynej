from __future__ import annotations

from ..core.base_agent import BaseAgent
from .personal_info import PersonalInfoAgent
from .experience import ExperienceAgent
from .hobbies import HobbiesAgent
from .behavioral import BehavioralQuestionAgent
from .resume import ResumeAgent
from .calendar import CalendarAgent
from .fallback import FallbackAgent


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
