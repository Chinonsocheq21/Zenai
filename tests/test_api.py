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
