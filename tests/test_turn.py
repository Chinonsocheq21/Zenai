"""The full turn with a FAKE language model -- no key needed, runs in CI.

The property that matters most is pinned first: a crisis message never
reaches the language model at all.
"""

import pytest

from zenai import llm
from zenai.agents import turn
from zenai.models import fidelity


@pytest.fixture
def fake_llm(monkeypatch):
    calls = []

    def fake_chat(messages, **kw):
        calls.append(messages)
        reply = fake_chat.replies.pop(0) if fake_chat.replies else "What is that like for you?"
        return {"text": reply, "model": "fake", "ms": 1, "tokens_in": 0, "tokens_out": 0}

    fake_chat.replies = []
    monkeypatch.setattr(llm, "chat", fake_chat)
    monkeypatch.setattr(llm, "available", lambda: True)
    monkeypatch.setattr(turn, "LOG", turn.LOG.parent / "turns.test.jsonl")
    return fake_chat, calls


def test_a_crisis_message_never_reaches_the_language_model(fake_llm):
    _, calls = fake_llm
    r = turn.run("I don't want to be here anymore")
    assert r["escalate"] is True
    assert calls == []                      # the model was never called
    assert r["reply"] is None and r["attempts"] == []


needs_models = pytest.mark.skipif(
    not fidelity.available(), reason="needs the trained drift detector and distress model")


@needs_models
def test_a_drifting_draft_is_rewritten_before_it_is_sent(fake_llm):
    fake, calls = fake_llm
    fake.replies = [
        "You've got this! Try breaking your notes into 25-minute blocks.",   # drifts
        # verified to pass the monitor (0.07 advice / 0.17 reassurance). NB: a reply that
        # merely MENTIONS closing the notes gets flagged as advice -- the known
        # false-rejection weakness, tracked as its own task.
        "Tell me more. What is it like for you, right now, sitting with this?",
    ]
    r = turn.run("I keep opening my notes and closing them")
    assert r["attempts"][0]["drift"] is True
    assert r["reply"].startswith("Tell me more")
    # the rewrite was told WHY the first draft was rejected
    assert "rejected by the Fidelity Monitor" in calls[1][-1]["content"]


@needs_models
def test_when_every_rewrite_drifts_the_safe_fallback_is_sent(fake_llm):
    fake, _ = fake_llm
    fake.replies = ["Don't worry, you'll do great!"] * 5
    r = turn.run("I have three exams and I cannot sleep")
    assert r["fallback"] is True
    from zenai.agents.conversation import SAFE_FALLBACK
    assert r["reply"] == SAFE_FALLBACK


@needs_models
def test_monitor_off_sends_the_first_draft_unchecked(fake_llm):
    fake, _ = fake_llm
    fake.replies = ["You've got this! Try breaking your notes into blocks."]
    r = turn.run("I keep opening my notes and closing them", monitor=False)
    assert r["reply"].startswith("You've got this") and r["attempts"][0]["checked"] is False
