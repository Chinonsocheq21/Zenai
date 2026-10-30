"""Usage limits, the class code, and feedback."""

import pytest
from fastapi.testclient import TestClient

from zenai.api import limits
from zenai.api.main import app
from zenai.config import settings

client = TestClient(app)
DEV = {"X-ZenAI-Device": "test-phone"}


@pytest.fixture(autouse=True)
def fresh(monkeypatch):
    limits.reset()
    monkeypatch.setattr(settings, "LIMIT_PER_10MIN", 2)
    monkeypatch.setattr(settings, "ACCESS_CODE", "")
    yield
    limits.reset()


def test_over_the_limit_is_a_calm_pause(monkeypatch):
    from zenai import llm
    from zenai.agents import turn

    monkeypatch.setattr(llm, "available", lambda: True)
    monkeypatch.setattr(turn, "run", lambda *a, **k: {"escalate": False, "reply": "ok", "redacted_text": "x"})
    for _ in range(2):
        assert client.post("/chat", json={"text": "hi"}, headers=DEV).status_code == 200
    r = client.post("/chat", json={"text": "hi again"}, headers=DEV)
    assert r.status_code == 429 and "988" in r.json()["detail"]["message"]


def test_a_crisis_is_answered_even_over_the_limit(monkeypatch):
    from zenai import llm
    from zenai.agents import turn

    monkeypatch.setattr(llm, "available", lambda: True)
    monkeypatch.setattr(turn, "run", lambda *a, **k: {"escalate": False, "reply": "ok", "redacted_text": "x"})
    for _ in range(2):
        client.post("/chat", json={"text": "hi"}, headers=DEV)
    r = client.post("/chat", json={"text": "I want to kill myself"}, headers=DEV)
    assert r.status_code == 200 and r.json()["escalate"] is True


def test_other_devices_are_not_affected(monkeypatch):
    from zenai import llm
    from zenai.agents import turn

    monkeypatch.setattr(llm, "available", lambda: True)
    monkeypatch.setattr(turn, "run", lambda *a, **k: {"escalate": False, "reply": "ok", "redacted_text": "x"})
    for _ in range(3):
        client.post("/chat", json={"text": "hi"}, headers=DEV)
    assert client.post("/chat", json={"text": "hi"}, headers={"X-ZenAI-Device": "other"}).status_code == 200


def test_class_code_is_required_when_set(monkeypatch):
    monkeypatch.setattr(settings, "ACCESS_CODE", "MORGAN-42")
    r = client.post("/chat", json={"text": "hi"}, headers=DEV)
    assert r.status_code == 401 and r.json()["detail"]["code_required"]


def test_feedback_is_recorded_and_summarised(tmp_path, monkeypatch):
    from zenai.api.routes import classroom

    monkeypatch.setattr(classroom, "FEEDBACK", tmp_path / "fb.jsonl")
    assert client.post("/feedback", json={"helpful": True, "specialist": "Academic Stress", "reply": "x"}, headers=DEV).json()["ok"]
    client.post("/feedback", json={"helpful": False}, headers=DEV)
    s = client.get("/feedback/summary").json()
    assert s["total"] == 2 and s["helpful"] == 1 and s["by_specialist"]["Academic Stress"]["helpful"] == 1


def test_present_page_and_qr():
    assert client.get("/present/").status_code == 200
    info = client.get("/present/info").json()
    assert info["url"].endswith("/student/")
    q = client.get("/qr.svg", params={"data": info["url"]})
    assert q.status_code == 200 and q.text.lstrip().startswith("<?xml") or "<svg" in q.text
