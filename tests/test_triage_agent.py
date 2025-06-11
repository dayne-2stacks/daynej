import os
import sys

os.environ["ANYIO_TEST_BACKENDS"] = "asyncio"

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from agents_ext.agents import TriageAgent
import pytest


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.mark.anyio
async def test_triage_personal_info(anyio_backend):
    agent = TriageAgent()
    result = await agent.run("What is your contact info?")
    assert "@usf.edu" in result


@pytest.mark.anyio
async def test_triage_fallback(anyio_backend):
    agent = TriageAgent()
    result = await agent.run("Tell me something unrelated.")
    assert "dayneguy@gmail.com" in result


@pytest.mark.anyio
async def test_triage_behavioral(anyio_backend, monkeypatch):
    agent = TriageAgent()

    class DummyMsg:
        def __init__(self, content: str) -> None:
            self.message = type("m", (), {"content": content})

    class DummyEmb:
        def __init__(self) -> None:
            self.embedding = [1.0, 0.0, 0.0]

    def fake_embed(model, input):
        class Resp:
            data = [DummyEmb()]

        return Resp()

    def fake_chat(model, messages):
        class Resp:
            choices = [DummyMsg("behavioral resp")]

        return Resp()

    monkeypatch.setattr(agent.behavioral.client.embeddings, "create", fake_embed)
    monkeypatch.setattr(
        agent.behavioral.client.chat.completions,
        "create",
        fake_chat,
    )

    result = await agent.run("Give me a behavioral interview question")
    assert "behavioral resp" in result


@pytest.mark.anyio
async def test_triage_resume(anyio_backend):
    agent = TriageAgent()
    result = await agent.run("Please generate a resume")
    assert "resume" in result.lower()


@pytest.mark.anyio
async def test_triage_calendar(anyio_backend):
    agent = TriageAgent()
    result = await agent.run("Set up a meeting tomorrow")
    assert "meeting" in result.lower()
