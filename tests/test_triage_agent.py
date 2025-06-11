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
