import os
import sys

import pytest

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from agents_ext.agents.experience import ExperienceAgent


@pytest.fixture
def anyio_backend():
    return "asyncio"


class DummyMessage:
    def __init__(self, content: str) -> None:
        self.message = type("msg", (), {"content": content})


class DummyEmbedding:
    def __init__(self) -> None:
        self.embedding = [1.0, 0.0, 0.0]


@pytest.mark.anyio
async def test_experience_agent(monkeypatch, anyio_backend):
    agent = ExperienceAgent()

    def fake_embed(model, input):
        class Resp:
            data = [DummyEmbedding()]

        return Resp()

    def fake_chat(model, messages):
        class Resp:
            choices = [DummyMessage("experience resp")]

        return Resp()

    monkeypatch.setattr(agent.client.embeddings, "create", fake_embed)
    monkeypatch.setattr(agent.client.chat.completions, "create", fake_chat)

    result = await agent.run("Tell me about your projects")
    assert "experience resp" in result
