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


def test_tunnel_requests_are_not_local(monkeypatch):
    """cloudflared connects from 127.0.0.1; its header must stop it passing as local."""
    from fastapi.testclient import TestClient

    from zenai.api.main import app
    from zenai.config import settings

    monkeypatch.setattr(settings, "ACCESS_CODE", "ZEN-1234")
    c = TestClient(app)
    via = {"cf-connecting-ip": "203.0.113.9"}
    assert c.get("/present/info", headers=via).status_code == 403
    assert c.get("/workflow/recent", headers=via).status_code == 403
    assert c.get("/feedback/summary", headers=via).status_code == 403
    assert c.get("/present/info").status_code == 200


def test_audit_for_teammates_needs_code_and_name(monkeypatch):
    from fastapi.testclient import TestClient

    from zenai.api.main import app
    from zenai.config import settings

    monkeypatch.setattr(settings, "ACCESS_CODE", "ZEN-1234")
    c = TestClient(app)
    via = {"cf-connecting-ip": "203.0.113.9"}
    assert c.get("/audit/items?tag=e1-v2", headers=via).status_code == 403          # no name
    assert c.get("/audit/items?tag=e1-v2&rater=abe", headers=via).status_code == 401  # no code
    ok = c.get("/audit/items?tag=e1-v2&rater=abe", headers={**via, "x-zenai-code": "zen-1234"})
    assert ok.status_code in (200, 404)            # 404 only where the sheet isn't checked in
