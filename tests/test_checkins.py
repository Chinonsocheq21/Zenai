"""Check-ins that follow an account, only when sync is on; limits that follow
the account, and fall back to the device when the database can't answer."""

from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient

from zenai.api import limits
from zenai.api.main import app
from zenai.api.routes import auth
from zenai.config import settings


@pytest.fixture(autouse=True)
def fresh(monkeypatch):
    auth.OUTBOX.clear()
    auth._migrated.cache_clear()
    limits.reset()
    monkeypatch.delenv("RESEND_API_KEY", raising=False)
    monkeypatch.delenv("VERCEL", raising=False)
    yield
    limits.reset()


def signed_in(email="kim@morgan.edu") -> TestClient:
    c = TestClient(app, follow_redirects=False)
    c.post("/auth/start", json={"email": email})
    c.post("/auth/verify", data={"token": auth.OUTBOX[-1]["link"].split("token=", 1)[1]})
    return c


TODAY = datetime.now(timezone.utc).date()


def test_needs_sign_in(pg):
    c = TestClient(app)
    assert c.get("/checkins").status_code == 401
    assert c.put("/checkins", json={"day": TODAY.isoformat(), "level": 1}).status_code == 401


def test_nothing_stored_until_sync_is_on(pg):
    c = signed_in()
    assert c.put("/checkins", json={"day": TODAY.isoformat(), "level": 1}).json() == {"stored": False}
    assert c.get("/checkins").json() == {"sync": False, "checkins": []}


def test_phone_and_laptop_see_the_same_checkins(pg):
    phone, laptop = signed_in(), signed_in()            # same student, two devices
    yday = TODAY - timedelta(days=1)
    r = phone.post("/checkins/sync", json={"on": True, "checkins": [{"day": yday.isoformat(), "level": 2}]})
    assert r.json() == {"sync": True, "uploaded": 1}
    assert phone.put("/checkins", json={"day": TODAY.isoformat(), "level": 0}).json() == {"stored": True}
    assert laptop.get("/checkins").json() == {"sync": True, "checkins": [
        {"day": yday.isoformat(), "level": 2}, {"day": TODAY.isoformat(), "level": 0}]}
    other = signed_in("lee@morgan.edu")
    assert other.get("/checkins").json()["checkins"] == []                 # nobody else's


def test_turning_sync_off_deletes_what_was_synced(pg):
    c = signed_in()
    c.post("/checkins/sync", json={"on": True, "checkins": [{"day": TODAY.isoformat(), "level": 3}]})
    assert c.post("/checkins/sync", json={"on": False}).json()["sync"] is False
    assert pg.execute("SELECT count(*) FROM checkins").fetchone()[0] == 0


def test_im_not_okay_is_never_a_stored_checkin_and_dates_are_sane(pg):
    c = signed_in()
    c.post("/checkins/sync", json={"on": True})
    assert c.put("/checkins", json={"day": TODAY.isoformat(), "level": 4}).status_code == 422
    far = (TODAY + timedelta(days=30)).isoformat()
    assert c.put("/checkins", json={"day": far, "level": 1}).status_code == 422


def test_limits_follow_the_account_across_devices(pg, monkeypatch):
    from zenai import llm
    from zenai.agents import turn

    monkeypatch.setattr(settings, "LIMIT_PER_10MIN", 2)
    monkeypatch.setattr(settings, "ACCESS_CODE", "")
    monkeypatch.setattr(llm, "available", lambda: True)
    monkeypatch.setattr(turn, "run", lambda *a, **k: {"escalate": False, "reply": "ok", "redacted_text": "x"})
    phone, laptop = signed_in(), signed_in()
    assert phone.post("/chat", json={"text": "hi"}, headers={"X-ZenAI-Device": "phone"}).status_code == 200
    assert laptop.post("/chat", json={"text": "hi"}, headers={"X-ZenAI-Device": "laptop"}).status_code == 200
    assert laptop.post("/chat", json={"text": "hi"}, headers={"X-ZenAI-Device": "laptop"}).status_code == 429
    r = phone.post("/chat", json={"text": "I want to end my life"}, headers={"X-ZenAI-Device": "phone"})
    assert r.status_code == 200 and r.json()["escalate"] is True          # a crisis is never limited


def test_limits_fall_back_to_the_device_when_the_database_is_down(monkeypatch):
    """No `pg`: a session cookie with no reachable database must not break chat."""
    from zenai import llm
    from zenai.agents import turn

    monkeypatch.setattr(llm, "available", lambda: True)
    monkeypatch.setattr(turn, "run", lambda *a, **k: {"escalate": False, "reply": "ok", "redacted_text": "x"})
    c = TestClient(app)
    c.cookies.set(auth.COOKIE, "stale-or-unreachable")
    assert c.post("/chat", json={"text": "hi"}, headers={"X-ZenAI-Device": "d1"}).status_code == 200
