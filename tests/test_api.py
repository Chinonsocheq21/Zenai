"""The safety ordering, pinned at the API boundary.

These run without a trained distress model, which is the point: the crisis
path must never depend on the mood model existing, loading, or being right.
"""

import pytest

fastapi = pytest.importorskip("fastapi")
from fastapi.testclient import TestClient

from zenai.api.main import app

client = TestClient(app)


def test_crisis_stops_the_turn_after_stage_two():
    d = client.post("/analyze", json={"text": "I don't want to be here anymore"}).json()
    assert d["escalate"] is True
    stages = [s["stage"] for s in d["trace"]]
    assert stages == ["privacy", "crisis", "mood", "memory", "conversation", "fidelity", "send"]
    status = {s["stage"]: s["status"] for s in d["trace"]}
    assert status["privacy"] == "done"
    assert status["crisis"] == "escalated"
    # nothing after the crisis rail runs -- no mood score, no draft, no reply
    assert all(status[s] == "skipped" for s in stages[2:])
    assert d["distress"] == {}
    assert d["escalation"]["hotline"] == "988"


def test_identifiers_are_redacted_before_anything_reads_them():
    d = client.post("/analyze", json={"text": "I don't want to be here anymore, email me at a@b.edu"}).json()
    assert "a@b.edu" not in d["redacted_text"]
    assert "[EMAIL]" in d["redacted_text"]


def test_console_is_served():
    r = client.get("/app/")
    assert r.status_code == 200
    assert "ZenAI" in r.text


def test_student_app_and_resources():
    r = client.get("/student/")
    assert r.status_code == 200 and "ZenAI" in r.text
    res = client.get("/resources").json()
    assert res["hotline"] == "988" and res["phone"]


def test_workflow_viewer_and_recent_events():
    assert client.get("/workflow/").status_code == 200
    r = client.get("/workflow/recent").json()
    assert "events" in r and "last" in r


def test_close_falls_back_when_no_model(monkeypatch):
    from zenai import llm

    monkeypatch.setattr(llm, "available", lambda: False)
    r = client.post("/chat/close", json={"history": []}).json()
    assert r["fallback"] is True and "come back" in r["reply"]


def test_audit_page_never_reveals_the_condition():
    import csv
    from pathlib import Path

    tags = [p.parent.name for p in Path("results/e1").glob("*/audit_replies.csv")]
    if not tags:
        return
    r = client.get(f"/audit/items?tag={tags[0]}").json()
    assert r["items"] and "monitor" not in str(r["items"][0]).lower()
    assert set(r["items"][0]) == {"id", "message", "reply"}
    assert csv  # the key lives in data/e1-keys, never served
