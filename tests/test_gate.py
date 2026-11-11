"""REQUIRE_SIGNIN: when hosted, a turn needs a session; invite codes get one
without an email. A crisis from a signed-out device always gets the hand-off."""

import pytest
from fastapi.testclient import TestClient

from zenai.api import limits
from zenai.api.main import app
from zenai.api.routes import auth
from zenai.config import settings

CODE = "launch-day-" + "x" * 10   # 20 chars, well over the 12 minimum


@pytest.fixture(autouse=True)
def fresh(monkeypatch):
    auth.OUTBOX.clear()
    auth._migrated.cache_clear()
    limits.reset()
    monkeypatch.setattr(settings, "REQUIRE_SIGNIN", True)
    monkeypatch.setenv("INVITE_CODES", f"launch:{CODE}")
    monkeypatch.delenv("VERCEL", raising=False)
    yield
    auth._migrated.cache_clear()


def client() -> TestClient:
    return TestClient(app, follow_redirects=False)


def test_crisis_while_signed_out_still_hands_off(pg, monkeypatch):
    from zenai import llm

    monkeypatch.setattr(llm, "available", lambda: False)
    r = client().post("/chat", json={"text": "I want to end my life"})
    assert r.status_code == 200
    assert r.json()["escalate"] is True


def test_normal_turn_while_signed_out_is_refused(pg):
    r = client().post("/chat", json={"text": "hi, how are you"})
    assert r.status_code == 401
    assert r.json()["detail"]["code"] == "signin_required"


def test_tts_while_signed_out_is_refused(pg):
    r = client().post("/tts", json={"text": "hello there"})
    assert r.status_code == 401
    assert r.json()["detail"]["code"] == "signin_required"


def test_flag_off_is_today_s_behaviour(pg, monkeypatch):
    from zenai import llm
    from zenai.agents import turn

    monkeypatch.setattr(settings, "REQUIRE_SIGNIN", False)
    monkeypatch.setattr(llm, "available", lambda: True)
    monkeypatch.setattr(turn, "run", lambda *a, **k: {"escalate": False, "reply": "ok", "redacted_text": "x"})
    r = client().post("/chat", json={"text": "hi, how are you"})
    assert r.status_code == 200


def test_invite_redeem_works_then_chat_is_allowed(pg, monkeypatch):
    from zenai import llm
    from zenai.agents import turn

    monkeypatch.setattr(llm, "available", lambda: True)
    monkeypatch.setattr(turn, "run", lambda *a, **k: {"escalate": False, "reply": "ok", "redacted_text": "x"})
    c = client()
    r = c.post("/auth/invite", json={"code": CODE})
    assert r.status_code == 200
    body = r.json()
    assert body["signed_in"] is True and body["campus"]
    assert "zenai_session" in r.headers["set-cookie"]
    assert c.get("/auth/me").json()["signed_in"] is True
    assert c.post("/chat", json={"text": "hi, how are you"}).status_code == 200


def test_invite_user_has_no_email(pg):
    c = client()
    c.post("/auth/invite", json={"code": CODE})
    row = pg.execute("SELECT email_hmac FROM users").fetchone()
    assert row[0] is None


def test_bad_invite_code_is_refused(pg):
    r = client().post("/auth/invite", json={"code": "not-a-real-code-at-all"})
    assert r.status_code == 403
    assert "zenai_session" not in r.headers.get("set-cookie", "")


def test_short_invite_codes_are_ignored(pg, monkeypatch):
    monkeypatch.setenv("INVITE_CODES", "launch:too-short")
    r = client().post("/auth/invite", json={"code": "too-short"})
    assert r.status_code == 403


def test_invite_is_rate_limited(pg, monkeypatch):
    monkeypatch.setattr(limits, "INVITE_PER_HOUR", 2)
    c = client()
    for _ in range(2):
        c.post("/auth/invite", json={"code": "wrong-code-wrong-code"})
    r = c.post("/auth/invite", json={"code": "wrong-code-wrong-code"})
    assert r.status_code == 429


def test_signed_in_student_passes_the_gate(pg, monkeypatch):
    from zenai import llm
    from zenai.agents import turn

    monkeypatch.setattr(llm, "available", lambda: True)
    monkeypatch.setattr(turn, "run", lambda *a, **k: {"escalate": False, "reply": "ok", "redacted_text": "x"})
    c = client()
    assert c.post("/auth/start", json={"email": "kim@morgan.edu"}).status_code == 200
    link = auth.OUTBOX[-1]["link"].replace("http://testserver", "")
    token = link.split("token=", 1)[1]
    c.post("/auth/verify", data={"token": token})
    assert c.post("/chat", json={"text": "hi, how are you"}).status_code == 200


def test_store_down_degrades_to_calm_503_for_non_crisis(monkeypatch):
    """No `pg` fixture: the database is unreachable (see conftest). A crisis still
    hands off; a normal turn gets a calm 503, not a 401."""
    from zenai import llm

    monkeypatch.setattr(llm, "available", lambda: False)
    c = client()
    crisis = c.post("/chat", json={"text": "I want to end my life"})
    assert crisis.status_code == 200 and crisis.json()["escalate"] is True
    normal = c.post("/chat", json={"text": "hi, how are you"})
    assert normal.status_code == 503
    assert "ZenAI" in normal.json()["detail"]["message"] or "keep using" in normal.json()["detail"]["message"]


def test_auth_me_reports_required():
    assert client().get("/auth/me").json()["required"] is True


def test_invite_code_ignores_case_and_spaces(monkeypatch):
    from zenai.api.routes import auth
    monkeypatch.setenv("INVITE_CODES", "class:abcd-efgh-ijkl-mnop")
    assert auth._invite_label("Abcd-EFGH-ijkl-mnop ") == "class"
    assert auth._invite_label("abcd efgh-ijkl-mnop") is None
    assert auth._invite_label("abcd-efgh-ijkl-mnoq") is None


def test_a_class_on_one_campus_network_can_all_sign_in(pg):
    # Campus Wi-Fi puts a whole class behind one IP address: 30 phones must get in.
    for i in range(30):
        r = client().post("/auth/invite", json={"code": CODE}, headers={"X-ZenAI-Device": f"phone-{i}"})
        assert r.status_code == 200, i
