"""Pilot requests: stored as written, emailed to the founder, never lost, bots dropped."""

import httpx
import pytest
from fastapi.testclient import TestClient

from zenai.api import limits
from zenai.api.main import app
from zenai.api.routes import pilot

OK = {"name": "Dr. Ada Lane", "email": "ada.lane@example.edu", "institution": "Example State University",
      "role": "Counseling Center Director", "message": "Interested in a spring pilot."}
NOTIFY = "founder@example.com"


class Resp:
    def __init__(self, status: int):
        self.status_code = status


@pytest.fixture(autouse=True)
def _clean(monkeypatch):
    limits.reset()
    pilot.reset()
    for k in ("KV_REST_API_URL", "KV_REST_API_TOKEN", "UPSTASH_REDIS_REST_URL", "UPSTASH_REDIS_REST_TOKEN",
              "RESEND_API_KEY", "NOTIFY_EMAIL", "MAIL_FROM", "VERCEL"):
        monkeypatch.delenv(k, raising=False)


@pytest.fixture
def mail(monkeypatch):
    """A fake Resend: records every email; `fail_to` addresses are refused (403)."""
    monkeypatch.setenv("RESEND_API_KEY", "re_test")
    monkeypatch.setenv("NOTIFY_EMAIL", NOTIFY)
    sent: list[dict] = []
    fail_to: set[str] = set()

    def post(url, json=None, headers=None, timeout=None, **_):
        assert url == pilot.RESEND and timeout == 10
        assert headers == {"Authorization": "Bearer re_test"}
        if fail_to & set(json["to"]):
            return Resp(403)
        sent.append(json)
        return Resp(200)

    monkeypatch.setattr(httpx, "post", post)
    post.sent, post.fail_to = sent, fail_to
    return post


def test_request_is_stored(pg):
    assert TestClient(app).post("/pilot", json=OK).json() == {"ok": True}
    row = pg.execute("SELECT name, email, institution, role, message FROM pilot_requests").fetchone()
    assert row == (OK["name"], OK["email"], OK["institution"], OK["role"], OK["message"])


def test_notification_has_every_field(pg, mail):
    assert TestClient(app).post("/pilot", json=OK).json() == {"ok": True}
    note = next(m for m in mail.sent if m["to"] == [NOTIFY])
    assert note["from"] == "ZenAI <onboarding@resend.dev>"
    assert note["reply_to"] == OK["email"]
    for v in OK.values():
        assert v in note["text"]
    confirm = next(m for m in mail.sent if m["to"] == [OK["email"]])
    assert "two business days" in confirm["text"] and NOTIFY not in confirm["text"]


def test_mail_from_is_used(pg, mail, monkeypatch):
    monkeypatch.setenv("MAIL_FROM", "ZenAI <hello@zenai.example>")
    TestClient(app).post("/pilot", json=OK)
    assert all(m["from"] == "ZenAI <hello@zenai.example>" for m in mail.sent) and mail.sent


def test_database_down_still_notifies(mail):
    r = TestClient(app).post("/pilot", json=OK)
    assert r.status_code == 200 and r.json() == {"ok": True}
    note = next(m for m in mail.sent if m["to"] == [NOTIFY])
    assert "ONLY in this email" in note["text"] and OK["message"] in note["text"]
    assert NOTIFY not in r.text


def test_confirmation_failure_does_not_fail(pg, mail):
    mail.fail_to.add(OK["email"])                    # Resend test sender: owner only
    assert TestClient(app).post("/pilot", json=OK).json() == {"ok": True}
    assert [m["to"] for m in mail.sent] == [[NOTIFY]]


def test_email_failure_does_not_fail_when_stored(pg, monkeypatch):
    monkeypatch.setenv("RESEND_API_KEY", "re_test")
    monkeypatch.setenv("NOTIFY_EMAIL", NOTIFY)

    def boom(*a, **k):
        raise httpx.ConnectTimeout("slow")

    monkeypatch.setattr(httpx, "post", boom)
    assert TestClient(app).post("/pilot", json=OK).json() == {"ok": True}
    assert pg.execute("SELECT count(*) FROM pilot_requests").fetchone()[0] == 1


def test_bots_and_bad_input(pg, mail):
    c = TestClient(app)
    assert c.post("/pilot", json={**OK, "website": "http://spam"}).json() == {"ok": True}
    assert pg.execute("SELECT count(*) FROM pilot_requests").fetchone()[0] == 0
    assert mail.sent == []
    assert c.post("/pilot", json={**OK, "email": "nope"}).status_code == 422
    assert c.post("/pilot", json={**OK, "name": ""}).status_code == 422
    assert mail.sent == []


def test_database_and_email_down_is_calm():
    r = TestClient(app).post("/pilot", json=OK)
    assert r.status_code == 503 and "try again later" in r.json()["detail"]["message"]


def test_own_rate_limit_bucket(pg):
    c = TestClient(app)
    for _ in range(pilot.PER_HOUR):
        assert c.post("/pilot", json=OK).status_code == 200
    assert c.post("/pilot", json=OK).status_code == 429
    assert not any(k[0] == "tts" for k in limits._hits)      # no longer borrows the tts bucket
