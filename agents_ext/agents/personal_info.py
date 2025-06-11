from __future__ import annotations

from ..core.base_agent import BaseAgent
from .utils import load_json


class PersonalInfoAgent(BaseAgent):
    """Provide contact and location information about Dayne."""

    def __init__(self) -> None:
        super().__init__("personal-info")
        self.data = load_json("dayne.json")

    async def run(self, message: str) -> str:
        text = message.lower()
        info = self.data["PersonalInformation"]
        if "contact" in text or "email" in text:
            return info["Contact"]
        if "location" in text or "where" in text:
            return info["Location"]
        return info["Name"]
