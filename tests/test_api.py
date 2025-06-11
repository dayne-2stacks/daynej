import os
import sys
import importlib
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import pytest

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from api import connection


class DummyRedis:
    def __init__(self):
        self.store = {}

    def ping(self):
        return True

    def exists(self, key):
        return key in self.store

    def expire(self, key, ttl):
        pass

    def setex(self, key, ttl, value):
        self.store[key] = value

    def get(self, key):
        return self.store.get(key)


class DummyManager:
    def __init__(self, model: str = "gpt-4o", registry=None) -> None:
        self.messages = []
        self.agent = object()
        self.input_list = []

    def add_message(self, role: str, content: str) -> None:
        self.messages.append((role, content))

    async def run_agent(self, instructions: str = "") -> None:
        self.messages.append(("assistant", "ok"))

    def create_agent(self, *args, **kwargs):
        pass

    def connect_confirm(self):
        return {"status": "ok"}

    def get_last_message(self):
        return "ok"


@pytest.fixture
def test_client(tmp_path, monkeypatch):
    db_path = tmp_path / "test.db"
    engine = create_engine(f"sqlite:///{db_path}")
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    monkeypatch.setattr(connection, "engine", engine, raising=False)
    monkeypatch.setattr(connection, "SessionLocal", SessionLocal, raising=False)
    connection.Base.metadata.create_all(bind=engine)

    monkeypatch.setitem(os.environ, "REDISCLOUD_URL", "redis://localhost:6379/0")
    monkeypatch.setattr("redis.Redis", lambda *a, **k: DummyRedis(), raising=False)

    api_module = importlib.import_module("api.api")
    importlib.reload(api_module)
    monkeypatch.setattr(api_module, "redis_client", DummyRedis(), raising=False)
    monkeypatch.setattr(api_module, "AgentManager", DummyManager, raising=False)

    client = TestClient(api_module.app)
    return client, connection


def test_register_persists_message(test_client):
    client, conn = test_client
    payload = {
        "fname": "John",
        "lname": "Doe",
        "email": "john@example.com",
        "reason": "test",
        "message": "hello",
    }
    response = client.post("/register", json=payload)
    assert response.status_code == 200
    assert client.cookies.get("session_id")

    with conn.SessionLocal() as db:
        rows = db.query(conn.Messages).all()
        assert len(rows) == 1
        assert rows[0].email == "john@example.com"


def test_chat_message_uses_existing_session(test_client):
    client, conn = test_client
    payload = {
        "fname": "Jane",
        "lname": "Doe",
        "email": "jane@example.com",
        "reason": "chat",
        "message": "hi",
    }
    register = client.post("/register", json=payload)
    session_id = register.cookies.get("session_id")

    response = client.post("/chat/message", json={"message": "second"})
    assert response.status_code == 200
    assert client.cookies.get("session_id") == session_id

    with conn.SessionLocal() as db:
        rows = db.query(conn.Messages).all()
        # Only the /register call persists
        assert len(rows) == 1


def test_chat_stream_sends_events(test_client, monkeypatch):
    client, _ = test_client

    class DummyEvent:
        item = object()

    class DummyStream:
        async def stream_events(self):
            yield DummyEvent()

        def to_input_list(self):
            return []

    async def dummy_run_streamed(agent, input_list):
        return DummyStream()

    from agents import run as agents_run
    from agents import ItemHelpers

    monkeypatch.setattr(agents_run.Runner, "run_streamed", dummy_run_streamed)
    monkeypatch.setattr(ItemHelpers, "text_message_outputs", lambda items: "chunk")

    payload = {
        "fname": "Jane",
        "lname": "Doe",
        "email": "jane@example.com",
        "reason": "chat",
        "message": "hi",
    }

    client.post("/register", json=payload)

    with client.stream("POST", "/chat/stream", json={"message": "hello"}) as r:
        assert r.status_code == 200
        assert r.headers["content-type"].startswith("text/event-stream")
