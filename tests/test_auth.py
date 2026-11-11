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
    monkeypatch.delenv("PUBLIC_URL", raising=False)
    yield
    auth._migrated.cache_clear()


def client() -> TestClient:
    return TestClient(app, follow_redirects=False)


def token_of(link: str) -> str:
    return link.split("token=", 1)[1]


def press(c: TestClient, token: str):
    """What the button on the sign-in page sends."""
    return c.post("/auth/verify", data={"token": token})


def sign_in(c: TestClient, email="kim@morgan.edu") -> None:
    assert c.post("/auth/start", json={"email": email}).status_code == 200
    link = auth.OUTBOX[-1]["link"]
    page = c.get(link.replace("http://testserver", ""))
    assert page.status_code == 200 and 'method="post"' in page.text
    r = press(c, token_of(link))
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
    assert c.get("/auth/me").json() == {"signed_in": True, "campus": "morgan.edu", "sync_checkins": False,
                                        "required": False}
    again = press(client(), token_of(auth.OUTBOX[-1]["link"]))
    assert again.headers["location"] == "/app/?signin=expired"
    assert press(client(), "made-up").headers["location"] == "/app/?signin=expired"
    assert client().post("/auth/verify").headers["location"] == "/app/?signin=expired"


def test_cookie_is_httponly_and_lax(pg):
    c = client()
    c.post("/auth/start", json={"email": "kim@morgan.edu"})
    r = press(c, token_of(auth.OUTBOX[-1]["link"]))
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
    assert c.get("/auth/me").json() == {"signed_in": False, "available": False, "required": False}
    monkeypatch.setattr(llm, "available", lambda: False)
    r = c.post("/chat", json={"text": "I want to end my life"})
    assert r.status_code == 200 and r.json()["escalate"] is True


def test_scanner_opening_the_link_leaves_it_usable(pg):
    """Safe Links / Proofpoint fetch the link first. That GET must not use the token."""
    c = client()
    c.post("/auth/start", json={"email": "kim@morgan.edu"})
    link = auth.OUTBOX[-1]["link"].replace("http://testserver", "")
    scanner = client()
    for _ in range(3):
        page = scanner.get(link)
        assert page.status_code == 200 and "set-cookie" not in page.headers
        assert "Sign in to ZenAI" in page.text and "<script" not in page.text.lower()
        assert " on" + "click" not in page.text.lower() and "http" not in page.text.split("<body>")[1]
    assert scanner.get("/auth/me").json()["signed_in"] is False
    assert press(c, token_of(link)).headers["location"] == "/app/?signin=ok"
    assert c.get("/auth/me").json()["signed_in"] is True


def test_page_does_not_reveal_whether_the_token_is_valid(pg):
    c = client()
    c.post("/auth/start", json={"email": "kim@morgan.edu"})
    real = token_of(auth.OUTBOX[-1]["link"])
    a, b = client().get(f"/auth/verify?token={real}"), client().get("/auth/verify?token=made-up")
    assert a.status_code == b.status_code == 200
    assert a.text.replace(real, "T") == b.text.replace("made-up", "T")
    assert a.headers["cache-control"] == "no-store"
    evil = client().get('/auth/verify?token="><b>x')
    assert '"><b>' not in evil.text and "&quot;&gt;&lt;b&gt;" in evil.text


def test_post_signs_in_once(pg):
    c = client()
    c.post("/auth/start", json={"email": "kim@morgan.edu"})
    tok = token_of(auth.OUTBOX[-1]["link"])
    first, second = press(client(), tok), press(client(), tok)
    assert first.headers["location"] == "/app/?signin=ok" and "zenai_session" in first.headers["set-cookie"]
    assert second.headers["location"] == "/app/?signin=expired" and "set-cookie" not in second.headers


def test_post_from_another_site_is_refused(pg):
    c = client()
    c.post("/auth/start", json={"email": "kim@morgan.edu"})
    tok = token_of(auth.OUTBOX[-1]["link"])
    r = client().post("/auth/verify", data={"token": tok}, headers={"Origin": "https://evil.example"})
    assert r.headers["location"] == "/app/?signin=expired" and "set-cookie" not in r.headers
    assert press(client(), tok).headers["location"] == "/app/?signin=ok"   # still usable by the student


def test_forged_host_does_not_change_the_emailed_link(pg, monkeypatch):
    monkeypatch.setenv("PUBLIC_URL", "https://zenai-app.vercel.app/")
    c = client()
    c.post("/auth/start", json={"email": "kim@morgan.edu"}, headers={"Host": "evil.example"})
    link = auth.OUTBOX[-1]["link"]
    assert link.startswith("https://zenai-app.vercel.app/auth/verify?token=") and "evil" not in link


def test_unset_public_url_only_trusts_local_requests(pg, monkeypatch):
    c = client()
    c.post("/auth/start", json={"email": "kim@morgan.edu"})
    assert auth.OUTBOX[-1]["link"].startswith("http://testserver/auth/verify?token=")   # on this machine
    c.post("/auth/start", json={"email": "lee@morgan.edu"},
           headers={"Host": "evil.example", "X-Forwarded-For": "203.0.113.9"})        # via a tunnel/proxy
    assert auth.OUTBOX[-1]["link"].startswith("https://zenai-app.vercel.app/auth/verify?token=")


def test_hosted_without_public_url_uses_the_production_address(pg, monkeypatch):
    import httpx

    sent = []
    monkeypatch.setenv("VERCEL", "1")
    monkeypatch.setenv("RESEND_API_KEY", "re_test")
    monkeypatch.setattr(httpx, "post", lambda url, json, headers, timeout: sent.append(json) or
                        httpx.Response(200, json={"id": "x"}, request=httpx.Request("POST", url)))
    client().post("/auth/start", json={"email": "kim@morgan.edu"}, headers={"Host": "evil.example"})
    assert "https://zenai-app.vercel.app/auth/verify?token=" in sent[0]["text"] and "evil" not in sent[0]["text"]
