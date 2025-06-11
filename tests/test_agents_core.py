import os
import sys
import asyncio

os.environ["ANYIO_TEST_BACKENDS"] = "asyncio"
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from agents_ext.core.base_agent import BaseAgent
from agents_ext.core.memory import Memory
from agents_ext.core.planner import Planner
from agents_ext.core.retrieval_agent import RetrievalAgent
from agents_ext.runner.run import AgentRunner
import pytest


@pytest.fixture
def anyio_backend():
    return "asyncio"


def test_memory_add_and_last():
    mem = Memory()
    mem.add("user", "hi")
    assert mem.last() == {"role": "user", "content": "hi"}


def test_planner_tasks():
    planner = Planner()
    planner.add_task("a")
    planner.add_task("b")
    assert planner.next_task() == "a"
    assert planner.next_task() == "b"
    assert planner.next_task() is None


@pytest.mark.anyio
async def test_base_agent_run(anyio_backend):
    if anyio_backend != "asyncio":
        pytest.skip("Requires asyncio backend")
    agent = BaseAgent("tester")
    runner = AgentRunner(agent)
    result = await runner.run("hello")
    assert result == "tester received: hello"
    assert agent.get_last_message() == "tester received: hello"


class DummyRetrievalAgent(RetrievalAgent):
    def __init__(self) -> None:
        data = [{"text": "one"}, {"text": "two"}]
        super().__init__("dummy", data=data, rerank_models=None)

    def _get_entry_text(self, entry: dict) -> str:  # type: ignore[override]
        return entry["text"]

    def _embed(self, text: str, model: str | None = None) -> list[float]:  # type: ignore[override]
        return [1.0, 0.0] if "one" in text else [0.0, 1.0]


def test_retrieval_agent_retrieve():
    agent = DummyRetrievalAgent()
    result = agent.retrieve("one", k=1)
    assert result[0]["text"] == "one"


if __name__ == "__main__":
    asyncio.run(test_base_agent_run())
