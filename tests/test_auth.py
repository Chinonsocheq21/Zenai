"""Sign-in by Morgan email link: the happy path, the abuse paths, and that
nothing else in ZenAI depends on it."""

import pytest
from fastapi.testclient import TestClient

from zenai.api import limits
from zenai.api.main import app
from zenai.api.routes import auth


@pytest.fixture(autouse=True)
def fresh(monkeypatch):
    auth.OUTBOX.clear()
    auth._migrated.cache_clear()
    limits.reset()
    monkeypatch.delenv("RESEND_API_KEY", raising=False)
    monkeypatch.delenv("VERCEL", raising=False)
    yield
    auth._migrated.cache_clear()


def client() -> TestClient:
    return TestClient(app, follow_redirects=False)


def sign_in(c: TestClient, email="kim@morgan.edu") -> None:
    assert c.post("/auth/start", json={"email": email}).status_code == 200
    link = auth.OUTBOX[-1]["link"]
    r = c.get(link.replace("http://testserver", ""))
    assert r.status_code == 303 and r.headers["location"] == "/app/?signin=ok"


def test_only_morgan_addresses(pg):
    c = client()
    for bad in ["kim@gmail.com", "kim@morgan.edu.evil.com", "not-an-email"]:
        assert c.post("/auth/start", json={"email": bad}).status_code == 422, bad
    assert c.post("/auth/start", json={"email": "kim@students.morgan.edu"}).status_code == 200
    assert not [m for m in auth.OUTBOX if "gmail" in m["to"]]


def test_link_signs_in_once(pg):
    c = client()
    sign_in(c)
    assert c.get("/auth/me").json() == {"signed_in": True, "campus": "morgan.edu", "sync_checkins": False}
    again = client().get(auth.OUTBOX[-1]["link"].replace("http://testserver", ""))
    assert again.headers["location"] == "/app/?signin=expired"
    assert client().get("/auth/verify?token=made-up").headers["location"] == "/app/?signin=expired"


def test_cookie_is_httponly_and_lax(pg):
    c = client()
    c.post("/auth/start", json={"email": "kim@morgan.edu"})
    r = c.get(auth.OUTBOX[-1]["link"].replace("http://testserver", ""))
    cookie = r.headers["set-cookie"].lower()
    assert "httponly" in cookie and "samesite=lax" in cookie and "path=/" in cookie


def test_same_answer_and_no_flood(pg):
    c = client()
    answers = {c.post("/auth/start", json={"email": "lee@morgan.edu"}).json()["message"] for _ in range(6)}
    assert len(answers) == 1                         # never reveals anything different
    assert len(auth.OUTBOX) == auth.PER_ADDRESS     # at most 3 links per address per 15 minutes


def test_signout_and_delete(pg):
    c = client()
    sign_in(c)
    c.post("/auth/signout")
    assert c.get("/auth/me").json()["signed_in"] is False
    sign_in(c, "del@morgan.edu")
    assert c.delete("/auth/account").json() == {"deleted": True}
    assert c.get("/auth/me").json()["signed_in"] is False
    assert pg.execute("SELECT count(*) FROM users").fetchone()[0] == 1   # only kim's, del@ is gone
    assert client().delete("/auth/account").status_code == 401


def test_hosted_without_email_key_says_so(pg, monkeypatch):
    monkeypatch.setenv("VERCEL", "1")
    r = client().post("/auth/start", json={"email": "kim@morgan.edu"})
    assert r.status_code == 503 and "set up" in r.json()["detail"]["message"]


def test_sends_through_resend_when_configured(pg, monkeypatch):
    import httpx

    sent = []

    def fake_post(url, json, headers, timeout):
        sent.append((url, json, headers))
        return httpx.Response(200, json={"id": "x"}, request=httpx.Request("POST", url))

    monkeypatch.setenv("RESEND_API_KEY", "re_test")
    monkeypatch.setattr(httpx, "post", fake_post)
    assert client().post("/auth/start", json={"email": "kim@morgan.edu"}).status_code == 200
    url, body, headers = sent[0]
    assert url == "https://api.resend.com/emails" and body["to"] == ["kim@morgan.edu"]
    assert headers["Authorization"] == "Bearer re_test"
    assert "/auth/verify?token=" in body["text"] and "988" in body["text"]
    assert not auth.OUTBOX


def test_database_down_is_calm_and_chat_still_works(monkeypatch):
    """No `pg` fixture: the database is unreachable (see conftest)."""
    from zenai import llm

    c = client()
    r = c.post("/auth/start", json={"email": "kim@morgan.edu"})
    assert r.status_code == 503 and "keep using ZenAI" in r.json()["detail"]["message"]
    c.cookies.set(auth.COOKIE, "something")
    assert c.get("/auth/me").json() == {"signed_in": False, "available": False}
    monkeypatch.setattr(llm, "available", lambda: False)
    r = c.post("/chat", json={"text": "I want to end my life"})
    assert r.status_code == 200 and r.json()["escalate"] is True
