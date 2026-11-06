"""Campus trends: counts only, small groups hidden, behind a pilot code, and
never in the way of a reply."""

import pytest
from fastapi.testclient import TestClient

from zenai import llm
from zenai.agents import turn
from zenai.api import limits
from zenai.api.main import app
from zenai.api.routes import aggregate, auth

CODE = "pilot-code-0123456789abcdef"


@pytest.fixture(autouse=True)
def fresh(monkeypatch):
    limits.reset()
    auth.OUTBOX.clear()
    auth._migrated.cache_clear()
    aggregate._down_until = 0.0
    aggregate._ready = False
    monkeypatch.setenv("PILOT_CODES", f"morgan.edu:{CODE}")
    monkeypatch.setattr(llm, "available", lambda: True)
    monkeypatch.setattr(turn, "run", lambda text, *a, **k: {
        "escalate": False, "reply": "ok", "redacted_text": text, "specialist": {"id": "academic"}})
    monkeypatch.setattr("zenai.config.settings.LIMIT_PER_10MIN", 1000)


def signed_in() -> TestClient:
    c = TestClient(app, follow_redirects=False)
    c.post("/auth/start", json={"email": "kim@morgan.edu"})
    c.get(auth.OUTBOX[-1]["link"].replace("http://testserver", ""))
    return c


def chat(c, text="secret words about my exam", history=None, checkin=None, client="student"):
    return c.post("/chat", json={"text": text, "history": history or [], "checkin": checkin, "client": client},
                  headers={"X-ZenAI-Device": "d"})


def trends(code=CODE):
    return TestClient(app).get("/aggregate", headers={"X-Pilot-Code": code})


def test_counts_only_no_text(pg):
    c = signed_in()
    chat(c, checkin="Heavy")
    dump = " ".join(str(r) for r in pg.execute("SELECT * FROM usage_weekly").fetchall())
    assert "secret" not in dump and "exam" not in dump
    metrics = {r[0]: r[1] for r in pg.execute("SELECT metric, n FROM usage_weekly WHERE campus='morgan.edu'")}
    assert metrics == {"messages": 1, "conversations": 1, "checkin:2": 1, "focus:academic": 1}


def test_only_the_real_app_is_counted(pg):
    c = signed_in()
    chat(c, client="smoke")
    chat(c, client="api")
    assert pg.execute("SELECT count(*) FROM usage_weekly").fetchone()[0] == 0


def test_signed_out_counts_as_open(pg):
    chat(TestClient(app))
    assert {r[0] for r in pg.execute("SELECT DISTINCT campus FROM usage_weekly")} == {"open"}


def test_small_groups_are_hidden(pg):
    c = signed_in()
    for i in range(12):
        chat(c, history=[] if i < 3 else [{"role": "user", "content": "x"}])
    week = trends().json()["weeks"][-1]
    assert week["messages"] == 12                 # 12 >= 10: shown
    assert week["conversations"] is None          # 3 < 10: hidden
    assert week["focus:academic"] == 12


def test_handoffs_are_counted(pg, monkeypatch):
    monkeypatch.setattr(llm, "available", lambda: False)     # crisis path without a model
    c = signed_in()
    for _ in range(10):
        chat(c, text="I want to end my life")
    assert trends().json()["weeks"][-1]["handoffs"] == 10


def test_pilot_code_required_and_scoped(pg, monkeypatch):
    assert trends("wrong-code-0123456789").status_code == 401
    assert TestClient(app).get("/aggregate").status_code == 401
    r = trends().json()
    assert r["campus"] == "morgan.edu" and r["min_group"] == 10 and len(r["weeks"]) == 8
    monkeypatch.setenv("PILOT_CODES", "morgan.edu:short")    # too short to count as a code
    assert trends("short").status_code == 401


def test_database_down_never_touches_the_reply():
    """No `pg`: counting fails quietly and backs off; the reply is unchanged."""
    c = TestClient(app)
    r = chat(c)
    assert r.status_code == 200 and r.json()["reply"] == "ok"
    assert aggregate._down_until > 0
    r = chat(c, text="I want to end my life")
    assert r.status_code == 200
