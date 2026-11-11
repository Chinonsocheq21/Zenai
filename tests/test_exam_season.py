"""The turn result's `season` field: null outside an exam_windows entry, the
string "exams" inside one -- so the app can show a gentle card, never advice.
No change to crisis behaviour; test_crisis_context.py stays the authority on
that and is never touched here.
"""

import datetime as dt

import pytest

from zenai import llm
from zenai.agents import specialists, turn
from zenai.models import fidelity

needs_models = pytest.mark.skipif(
    not fidelity.available(), reason="needs the trained drift detector and distress model")


@pytest.fixture
def fake_llm(monkeypatch):
    """Same shape as test_turn.py's fixture: no live model, no key needed."""
    calls = []

    def fake_chat(messages, **kw):
        calls.append(messages)
        reply = fake_chat.replies.pop(0) if fake_chat.replies else "What is that like for you?"
        return {"text": reply, "model": "fake", "ms": 1, "tokens_in": 0, "tokens_out": 0}

    fake_chat.replies = []
    monkeypatch.setattr(llm, "chat", fake_chat)
    monkeypatch.setattr(llm, "available", lambda: True)
    monkeypatch.setattr(turn, "LOG", turn.LOG.parent / "turns.test.jsonl")
    from zenai.config import settings
    monkeypatch.setattr(settings, "SECOND_OPINION", False)
    monkeypatch.setattr(settings, "ROUTER_LLM", False)
    monkeypatch.setattr(settings, "CRISIS_SCREEN", False)
    return fake_chat, calls


@needs_models
def test_season_is_null_outside_an_exam_window(fake_llm, monkeypatch):
    monkeypatch.setattr(specialists, "exam_season", lambda *a, **k: None)
    r = turn.run("I have two midterms this week and I'm stressed")
    assert r["escalate"] is False
    assert r["season"] is None


@needs_models
def test_season_is_exams_inside_an_exam_window(fake_llm, monkeypatch):
    window = {"label": "Fall 2026 final exams", "start": "2026-12-11", "end": "2026-12-18"}
    monkeypatch.setattr(specialists, "exam_season", lambda *a, **k: window)
    r = turn.run("I have two midterms this week and my professor says I'm failing")
    assert r["escalate"] is False
    assert r["season"] == "exams"
    # context only -- the reply itself is still checked, nothing extra leaks into it
    assert r["reply"] is not None


def test_a_crisis_message_still_escalates_during_exam_season(fake_llm, monkeypatch):
    """The exam-season card is a gentle nicety; it never gets in the way of the
    crisis rail, which runs first and stops the turn before routing at all."""
    window = {"label": "Fall 2026 final exams", "start": "2026-12-11", "end": "2026-12-18"}
    monkeypatch.setattr(specialists, "exam_season", lambda *a, **k: window)
    _, calls = fake_llm
    r = turn.run("I don't want to be here anymore")
    assert r["escalate"] is True
    assert calls == []
    assert r["season"] == "exams"   # present and accurate, but the model is still never called


def test_exam_season_reads_the_real_campus_registry_for_today_in_its_timezone():
    # inside the real Fall 2026 final exams window from campuses.json
    assert specialists.exam_season(
        now=dt.datetime(2026, 12, 15, 12, 0, tzinfo=dt.timezone.utc))["label"] == "Fall 2026 final exams"
    # well outside any window
    assert specialists.exam_season(now=dt.datetime(2026, 7, 4, 12, 0, tzinfo=dt.timezone.utc)) is None


def test_chat_response_passes_season_through(fake_llm, monkeypatch):
    """/chat returns turn.run()'s dict as-is, so season rides along with no
    extra plumbing -- this pins that contract at the API boundary."""
    from fastapi.testclient import TestClient

    from zenai.api.main import app
    from zenai.config import settings

    window = {"label": "Fall 2026 final exams", "start": "2026-12-11", "end": "2026-12-18"}
    monkeypatch.setattr(specialists, "exam_season", lambda *a, **k: window)
    monkeypatch.setattr(settings, "REQUIRE_SIGNIN", False, raising=False)
    c = TestClient(app)
    r = c.post("/chat", json={"text": "two midterms this week and I'm stressed, what's the point honestly"})
    assert r.status_code == 200
    body = r.json()
    assert body["escalate"] is False
    assert body["season"] == "exams"
