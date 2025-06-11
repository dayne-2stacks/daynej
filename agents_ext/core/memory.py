from __future__ import annotations
from typing import Dict, List


class Memory:
    """Simple in-memory storage for agent messages."""

    def __init__(self) -> None:
        self.messages: List[Dict[str, str]] = []

    def add(self, role: str, content: str) -> None:
        self.messages.append({"role": role, "content": content})

    def last(self) -> Dict[str, str] | None:
        return self.messages[-1] if self.messages else None

    def clear(self) -> None:
        self.messages.clear()
