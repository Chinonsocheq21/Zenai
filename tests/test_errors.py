"""Error reports never carry what a student wrote, and an unexpected failure
never skips the crisis check."""

import logging

import pytest
from fastapi.testclient import TestClient

from zenai import llm
from zenai.agents import turn
from zenai.api import limits
from zenai.api.main import app

SECRET = "my roommate Jordan and I fought about my exam"


@pytest.fixture(autouse=True)
def setup(monkeypatch):
    limits.reset()
    monkeypatch.setattr(llm, "available", lambda: True)

    def boom(text, *a, **k):
        raise RuntimeError(f"failed while handling: {text}")    # the kind of message that would leak

    monkeypatch.setattr(turn, "run", boom)


def client():
    return TestClient(app, raise_server_exceptions=False)


def test_error_report_has_no_message_text(caplog):
    caplog.set_level(logging.ERROR, logger="zenai.errors")
    r = client().post("/chat", json={"text": SECRET}, headers={"X-ZenAI-Device": "e1"})
    assert r.status_code == 500
    assert "988" in r.json()["detail"]["message"] and "Jordan" not in r.text
    logged = " ".join(rec.getMessage() for rec in caplog.records)
    assert '"route": "/chat"' in logged and '"type": "RuntimeError"' in logged
    for word in ("Jordan", "roommate", "exam", "failed while handling"):
        assert word not in logged


def test_unexpected_failure_still_hands_off_a_crisis():
    r = client().post("/chat", json={"text": "I want to end my life"}, headers={"X-ZenAI-Device": "e2"})
    assert r.status_code == 200 and r.json()["escalate"] is True
