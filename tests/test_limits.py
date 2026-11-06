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


class FakeUpstash:
    """Stands in for Upstash's REST pipeline: shared counts, like one Redis."""

    def __init__(self, fail=False):
        self.n, self.fail, self.calls = {}, fail, 0

    def post(self, url, json, headers, timeout):
        import httpx

        self.calls += 1
        if self.fail:
            raise httpx.ConnectError("down")
        out = []
        for cmd in json:
            if cmd[0] == "GET":
                out.append({"result": str(self.n[cmd[1]]) if cmd[1] in self.n else None})
            elif cmd[0] == "INCR":
                self.n[cmd[1]] = self.n.get(cmd[1], 0) + 1
                out.append({"result": self.n[cmd[1]]})
            else:
                out.append({"result": 1})
        req = httpx.Request("POST", url)
        return httpx.Response(200, json=out, request=req)


def _redis_env(monkeypatch, fake):
    import httpx

    monkeypatch.setenv("KV_REST_API_URL", "https://example.upstash.io")
    monkeypatch.setenv("KV_REST_API_TOKEN", "test-token")
    monkeypatch.setattr(httpx, "post", fake.post)


def test_limits_are_shared_through_redis(monkeypatch):
    """Two server instances (memory cleared between calls) still share one allowance."""
    fake = FakeUpstash()
    _redis_env(monkeypatch, fake)
    from starlette.requests import Request

    req = Request({"type": "http", "headers": [(b"x-zenai-device", b"phone-1")], "client": ("1.2.3.4", 1)})
    assert limits.allow(req)
    limits.reset()                          # a different instance: empty memory
    assert limits.allow(req)
    limits.reset()
    assert not limits.allow(req)            # cap is 2 in this test file
    assert not any("phone-1" in k for k in fake.n)   # device ids are hashed


def test_redis_down_falls_back_and_crisis_still_answered(monkeypatch):
    _redis_env(monkeypatch, FakeUpstash(fail=True))
    from zenai import llm
    from zenai.agents import turn

    monkeypatch.setattr(llm, "available", lambda: True)
    monkeypatch.setattr(turn, "run", lambda *a, **k: {"escalate": False, "reply": "ok", "redacted_text": "x"})
    h = {"X-ZenAI-Device": "phone-2"}
    assert client.post("/chat", json={"text": "hi"}, headers=h).status_code == 200
    assert client.post("/chat", json={"text": "hi"}, headers=h).status_code == 200
    assert client.post("/chat", json={"text": "hi"}, headers=h).status_code == 429   # memory limit held
    r = client.post("/chat", json={"text": "I want to end my life"}, headers=h)
    assert r.status_code == 200 and r.json()["escalate"] is True


def test_nothing_is_local_on_vercel(monkeypatch):
    monkeypatch.setenv("VERCEL", "1")
    assert client.get("/present/info").status_code == 403
    assert client.get("/workflow/recent").status_code == 403


def test_a_capped_device_does_not_drain_the_daily_total(monkeypatch):
    """Retries from a device that is already over its cap are refused AND not counted."""
    fake = FakeUpstash()
    _redis_env(monkeypatch, fake)
    from starlette.requests import Request

    req = Request({"type": "http", "headers": [(b"x-zenai-device", b"stuck-client")], "client": ("1.2.3.4", 1)})
    allowed = [limits.allow(req) for _ in range(50)]
    assert allowed.count(True) == 2
    day = [v for k, v in fake.n.items() if k.startswith("zl:global:")]
    assert day == [2]                       # 48 refused retries counted nowhere


def test_hosted_service_keeps_no_turn_log_or_feedback_file(monkeypatch, tmp_path):
    from zenai.agents import turn
    from zenai.api.routes import classroom

    monkeypatch.setenv("VERCEL", "1")
    monkeypatch.setattr(turn, "LOG", tmp_path / "turns.jsonl")
    monkeypatch.setattr(classroom, "FEEDBACK", tmp_path / "fb.jsonl")
    turn._log({"redacted_text": "x", "escalate": False}, True)
    r = client.post("/feedback", json={"helpful": True, "reply": "ok"}, headers=DEV)
    assert r.status_code == 200 and r.json()["stored"] is False
    assert not (tmp_path / "turns.jsonl").exists() and not (tmp_path / "fb.jsonl").exists()
