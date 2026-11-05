"""Smoke test for a deployed ZenAI (a Vercel preview or production).

    python tools/smoke.py https://zenai.vercel.app          # the checks below
    python tools/smoke.py https://zenai.vercel.app --limits # also hit the usage cap
    python tools/smoke.py --self-test                       # same checks, in-process

Checks, in order of how much they matter:
  1. a synthetic crisis message gets the hand-off (escalate: true)
  2. the student app loads at /app/
  3. /api/health answers and the models loaded
  4. an ordinary message gets a reply
  5. the laptop-only pages are closed (class code, workflow viewer)
  6. (--limits) one device is paused with 429 once it passes the 10-minute cap,
     and a crisis is still answered after that. Costs about 20 model calls.

Standard library only, so it runs anywhere. Messages are synthetic.
"""

from __future__ import annotations

import json
import sys
import urllib.error
import urllib.request
import uuid

CRISIS = "synthetic smoke test: I don't see the point of being here anymore"
ORDINARY = "synthetic smoke test: long week, I'm behind on everything"


class Http:
    def __init__(self, base: str):
        self.base = base.rstrip("/")

    def req(self, method: str, path: str, body: dict | None = None, headers: dict | None = None):
        data = json.dumps(body).encode() if body is not None else None
        h = {"Content-Type": "application/json", "User-Agent": "zenai-smoke/1", **(headers or {})}
        r = urllib.request.Request(self.base + path, data=data, headers=h, method=method)
        try:
            with urllib.request.urlopen(r, timeout=60) as resp:
                return resp.status, resp.read().decode("utf-8", "replace")
        except urllib.error.HTTPError as e:
            return e.code, e.read().decode("utf-8", "replace")


class InProcess:
    """The deployed shape (api/index.py), run here with the model stubbed out."""

    def __init__(self):
        import os

        os.environ["VERCEL"] = "1"      # behave exactly as the hosted function does
        sys.path[:0] = ["src", "."]
        from starlette.testclient import TestClient

        from zenai import llm
        from zenai.agents import turn
        from zenai.api import limits

        llm.available = lambda: True
        real = turn.run

        def fake(text, *a, **k):        # the real turn would call the model; the crisis path never does
            if "point of being here" in text:
                return real(text, *a, **k)
            return {"escalate": False, "reply": "That sounds like a lot. What matters most right now?",
                    "redacted_text": text}

        turn.run = fake
        limits.reset()
        import api.index as entry

        self.c = TestClient(entry.app)
        self.app_page = '<!DOCTYPE html><html><title>ZenAI</title>'   # Vercel serves /app statically

    def req(self, method, path, body=None, headers=None):
        if path.startswith("/app/"):
            return 200, self.app_page
        r = self.c.request(method, path, json=body, headers=headers or {})
        return r.status_code, r.text


def run(c, limits_too: bool = False) -> list[tuple[bool, str]]:
    out = []
    dev = {"X-ZenAI-Device": "smoke-" + uuid.uuid4().hex[:12]}

    s, t = c.req("POST", "/api/chat", {"text": CRISIS, "client": "smoke"}, dev)
    out.append((s == 200 and json.loads(t).get("escalate") is True, f"crisis hand-off ({s})"))

    s, t = c.req("GET", "/app/")
    out.append((s == 200 and "ZenAI" in t, f"student app loads ({s})"))

    s, t = c.req("GET", "/api/health")
    ok = s == 200 and json.loads(t).get("models") == "ok"
    out.append((ok, f"health and models ({s})"))

    s, t = c.req("POST", "/api/chat", {"text": ORDINARY, "client": "smoke"}, dev)
    d = json.loads(t) if s == 200 else {}
    out.append((s == 200 and not d.get("escalate") and bool(d.get("reply")), f"ordinary reply ({s})"))

    for path in ("/api/present/info", "/api/workflow/recent"):
        s, _ = c.req("GET", path)
        out.append((s in (403, 404), f"{path} closed ({s})"))

    if limits_too:
        statuses = []
        for _ in range(40):
            s, _ = c.req("POST", "/api/chat", {"text": ORDINARY, "client": "smoke"}, dev)
            statuses.append(s)
            if s == 429:
                break
        out.append((429 in statuses, f"usage cap reached after {len(statuses)} more messages"))
        s, t = c.req("POST", "/api/chat", {"text": CRISIS, "client": "smoke"}, dev)
        out.append((s == 200 and json.loads(t).get("escalate") is True, f"crisis answered over the cap ({s})"))
    return out


def main(argv: list[str]) -> int:
    if not argv or argv[0] in ("-h", "--help"):
        print(__doc__)
        return 2
    limits_too = "--limits" in argv
    if argv[0] == "--self-test":
        c, where = InProcess(), "in-process"
    else:
        c, where = Http(argv[0]), argv[0]
    results = run(c, limits_too or argv[0] == "--self-test")
    print(f"ZenAI smoke test: {where}")
    for ok, label in results:
        print(("  PASS  " if ok else "  FAIL  ") + label)
    failed = sum(not ok for ok, _ in results)
    print("all passed" if not failed else f"{failed} failed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
