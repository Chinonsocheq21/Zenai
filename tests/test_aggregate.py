"""Campus trends: counts only, small groups hidden, behind a pilot code, and
never in the way of a reply."""

from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient

from zenai import llm
from zenai.agents import turn
from zenai.api import limits
from zenai.api.main import app
from zenai.api.routes import aggregate, auth

CODE = "pilot-code-0123456789abcdef"

# Wednesday, 10:00 in America/New_York (campus timezone) -- inside the
# counseling office's published Mon-Fri 08:30-17:00 hours, and fixed so a
# metric that depends on the clock never flakes depending on when the suite runs.
NOW = datetime(2026, 1, 7, 15, 0, tzinfo=timezone.utc)
# Saturday -- the office is never open, whatever the hour.
AFTER_HOURS_NOW = datetime(2026, 1, 10, 15, 0, tzinfo=timezone.utc)


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
    monkeypatch.setattr(aggregate, "_now", lambda: NOW)


def signed_in() -> TestClient:
    c = TestClient(app, follow_redirects=False)
    c.post("/auth/start", json={"email": "kim@morgan.edu"})
    c.post("/auth/verify", data={"token": auth.OUTBOX[-1]["link"].split("token=", 1)[1]})
    return c


def chat(c, text="secret words about my exam", history=None, checkin=None, client="student"):
    return c.post("/chat", json={"text": text, "history": history or [], "checkin": checkin, "client": client},
                  headers={"X-ZenAI-Device": "d"})


def trends(code=CODE):
    return TestClient(app).get("/aggregate", headers={"X-Pilot-Code": code})


def metrics_for(pg, campus="morgan.edu") -> dict:
    return {r[0]: r[1] for r in pg.execute("SELECT metric, n FROM usage_weekly WHERE campus=%s", (campus,))}


def test_counts_only_no_text(pg):
    c = signed_in()
    chat(c, checkin="Heavy")
    dump = " ".join(str(r) for r in pg.execute("SELECT * FROM usage_weekly").fetchall())
    assert "secret" not in dump and "exam" not in dump
    metrics = metrics_for(pg)
    assert metrics == {"messages": 1, "conversations": 1, "checkin:2": 1, "focus:academic": 1,
                        "signed_in": 1, "speed:fast": 1}


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
    week = trends().json()["weeks"][-1]
    assert week["handoffs"] == 10
    assert week["handoff_by:patterns"] == 10                 # the message alone, no earlier context


def test_handoff_by_context_from_an_earlier_message(pg, monkeypatch):
    """No model (crisis-only path): a casual message still escalates because an
    earlier message in the same conversation was a crisis sign -- that is a
    context escalation, not the message alone."""
    monkeypatch.setattr(llm, "available", lambda: False)
    c = signed_in()
    for _ in range(10):
        r = chat(c, text="anyway hows ur day going",
                  history=[{"role": "user", "content": "everyone would be better off without me"}])
        assert r.json()["escalate"] is True
    metrics = metrics_for(pg)
    assert metrics["handoffs"] == 10
    assert metrics["handoff_by:context"] == 10
    assert "handoff_by:patterns" not in metrics


def test_handoff_by_screen_from_the_full_turn_trace(pg, monkeypatch):
    """When the full turn runs, the crisis stage's trace carries the model
    screen's reasoning; that is read straight off the trace (no second guess)."""
    def escalate_via_screen(text, *a, **k):
        return {"escalate": True, "crisis_risk": 0.55, "redacted_text": text, "reply": None, "attempts": [],
                "trace": [{"stage": "crisis", "status": "escalated", "ms": 1.0,
                           "detail": "risk 0.55 vs threshold 0.50 · model screen: elevated (indirect risk words)"}],
                "season": None, "note": "ok"}

    monkeypatch.setattr(turn, "run", escalate_via_screen)
    c = signed_in()
    chat(c, text="something indirect")
    metrics = metrics_for(pg)
    assert metrics["handoffs"] == 1
    assert metrics["handoff_by:screen"] == 1


def test_checked_first_pass_rewritten_and_fallback(pg, monkeypatch):
    def first_pass(text, *a, **k):
        return {"escalate": False, "reply": "ok", "redacted_text": text, "specialist": {"id": "academic"},
                "attempts": [{"draft": "ok", "checked": True, "drift": False}], "fallback": False}

    def rewritten(text, *a, **k):
        return {"escalate": False, "reply": "ok", "redacted_text": text, "specialist": {"id": "academic"},
                "attempts": [{"draft": "bad", "checked": True, "drift": True},
                             {"draft": "ok", "checked": True, "drift": False}], "fallback": False}

    def fell_back(text, *a, **k):
        return {"escalate": False, "reply": "safe", "redacted_text": text, "specialist": {"id": "academic"},
                "attempts": [{"draft": "bad", "checked": True, "drift": True}], "fallback": True}

    def unchecked(text, *a, **k):          # monitor=False (experiment E1 baseline)
        return {"escalate": False, "reply": "ok", "redacted_text": text, "specialist": {"id": "academic"},
                "attempts": [{"draft": "ok", "checked": False}], "fallback": False}

    c = signed_in()
    for fn in (first_pass, rewritten, fell_back, unchecked):
        monkeypatch.setattr(turn, "run", fn)
        chat(c)
    metrics = metrics_for(pg)
    assert metrics["checked"] == 3              # every run but the unchecked one
    assert metrics["first_pass"] == 1
    assert metrics["rewritten"] == 2             # the rewritten run and the one that fell back after a rewrite
    assert metrics["fallback"] == 1


def test_after_hours(pg, monkeypatch):
    c = signed_in()
    chat(c)                                              # inside office hours: not counted
    monkeypatch.setattr(aggregate, "_now", lambda: AFTER_HOURS_NOW)
    chat(c)                                              # Saturday: after hours
    metrics = metrics_for(pg)
    assert metrics["after_hours"] == 1
    assert metrics["messages"] == 2


def test_signed_in_vs_open(pg):
    chat(signed_in())
    chat(TestClient(app))
    assert metrics_for(pg, "morgan.edu").get("signed_in") == 1
    assert "signed_in" not in metrics_for(pg, "open")


def test_speed_buckets(pg, monkeypatch):
    from zenai.api.routes import chat as chat_route

    c = signed_in()
    for ms, bucket in ((1000.0, "fast"), (5000.0, "ok"), (9000.0, "slow")):
        monkeypatch.setattr(chat_route, "_elapsed_ms", lambda t0, ms=ms: ms)
        chat(c)
    metrics = metrics_for(pg)
    assert metrics["speed:fast"] == 1 and metrics["speed:ok"] == 1 and metrics["speed:slow"] == 1


def test_speed_bucket_boundaries():
    assert aggregate._speed_bucket(2999) == "fast"
    assert aggregate._speed_bucket(3000) == "ok"
    assert aggregate._speed_bucket(8000) == "ok"
    assert aggregate._speed_bucket(8000.1) == "slow"
    assert aggregate._speed_bucket(None) is None


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


def test_demo_needs_no_code_and_touches_no_database():
    """No `pg` fixture here either: the demo endpoint must not need the database."""
    r = TestClient(app).get("/aggregate/demo")
    assert r.status_code == 200
    body = r.json()
    assert body["campus"] == "demo" and body["demo"] is True and body["min_group"] == aggregate.MIN_GROUP
    assert len(body["weeks"]) == aggregate.DEMO_WEEKS


def test_demo_is_deterministic_and_has_some_hidden_cells():
    a, b = TestClient(app).get("/aggregate/demo").json(), TestClient(app).get("/aggregate/demo").json()
    assert a == b                                              # same shape every time, no randomness
    cells = [v for week in a["weeks"] for k, v in week.items() if k != "week"]
    assert any(v is None for v in cells)                       # some groups under 10: "fewer than 10"
    assert any(isinstance(v, int) and v >= aggregate.MIN_GROUP for v in cells)
    assert all(v is None or isinstance(v, int) for v in cells)  # never text


def test_demo_weeks_are_consecutive_and_unauthenticated():
    weeks = [w["week"] for w in TestClient(app).get("/aggregate/demo").json()["weeks"]]
    assert len(weeks) == len(set(weeks))
    from datetime import date as _date

    parsed = [_date.fromisoformat(w) for w in weeks]
    assert parsed == sorted(parsed)
    assert all((b - a).days == 7 for a, b in zip(parsed, parsed[1:]))
