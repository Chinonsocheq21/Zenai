"""The crisis check reads the conversation, and context only ever raises risk."""

import pytest

from zenai.config import settings
from zenai.models import crisis


def assess(*a, **k):
    """The pattern and context rules alone; the model screen is tested below with a stub."""
    return crisis.assess(*a, screen=False, **k)


T = settings.CRISIS_THRESHOLD


def test_indirect_sign_alone_does_not_stop_the_conversation():
    assert assess("honestly what's the point of this class")["risk"] < T


def test_indirect_sign_escalates_with_earlier_warning():
    a = assess("I don't see the point anymore", earlier=["everything is falling apart", "my mom yelled again"])
    assert a["risk"] >= T and "earlier" in a["why"]


def test_indirect_sign_escalates_with_heavy_checkin():
    assert assess("I just want it all to stop", checkin="Very heavy")["risk"] >= T
    assert assess("I just want it all to stop", checkin="Light")["risk"] < T


def test_context_never_lowers_risk():
    assert assess("I want to kill myself", earlier=["great day!"], checkin="Light")["risk"] >= T


def test_slang_and_goodbye_signals():
    for s in ["ngl i might kms", "I won't be around much longer", "I'm giving away all my stuff",
              "I want to go to sleep and never wake up", "i think i'm going to end it tonight"]:
        assert assess(s)["risk"] >= T, s


def test_only_three_recent_messages_count():
    old = ["I feel numb", "ok", "the game was fun", "lunch was good"]
    assert assess("what's the point", earlier=old)["risk"] < T


def test_earlier_crisis_keeps_the_conversation_in_crisis():
    a = assess("anyway hows ur day going", earlier=["everyone would be better off without me"])
    assert a["risk"] >= T and "earlier message" in a["why"]


def test_model_screen_only_raises(monkeypatch):
    from zenai.models import crisis_screen

    monkeypatch.setattr(crisis_screen, "screen", lambda t, e=None: {"risk": 0.99, "level": "high", "why": "pills"})
    assert crisis.assess("i keep looking at my pills")["risk"] >= T
    monkeypatch.setattr(crisis_screen, "screen", lambda t, e=None: {"risk": 0.02, "level": "none", "why": ""})
    assert crisis.assess("I want to kill myself")["risk"] >= T          # never talked down
    monkeypatch.setattr(crisis_screen, "screen", lambda t, e=None: {"risk": None, "error": "down"})
    assert "unavailable" in crisis.assess("hello there")["why"]


def test_explicit_crisis_never_reaches_the_screen(monkeypatch):
    from zenai.models import crisis_screen

    def boom(*a, **k):
        raise AssertionError("screen should not run")
    monkeypatch.setattr(crisis_screen, "screen", boom)
    assert crisis.assess("I want to kill myself")["risk"] >= T


def test_crisis_handoff_without_language_model(monkeypatch):
    """No key, or the model is down: a crisis still gets the hand-off, not an error."""
    from fastapi.testclient import TestClient

    from zenai import llm
    from zenai.api.main import app

    monkeypatch.setattr(llm, "available", lambda: False)
    c = TestClient(app)
    r = c.post("/chat", json={"text": "I want to end my life"})
    assert r.status_code == 200 and r.json()["escalate"] is True
    r = c.post("/chat", json={"text": "long day, just tired"})
    assert r.status_code == 503 and "988" in r.json()["detail"]["message"]


def test_crisis_handoff_when_model_errors(monkeypatch):
    from fastapi.testclient import TestClient

    from zenai import llm
    from zenai.agents import turn
    from zenai.api.main import app

    monkeypatch.setattr(llm, "available", lambda: True)

    def boom(*a, **k):
        raise llm.LLMError("down")

    monkeypatch.setattr(turn, "run", boom)
    r = TestClient(app).post("/chat", json={"text": "I want to end my life"})
    assert r.status_code == 200 and r.json()["escalate"] is True


def test_passive_ideation_caught_by_rules_alone():
    """The model screen usually catches these; the rules must too, for when it can't run."""
    from zenai.models.crisis import assess

    for t in ["I don't see the point of being here anymore", "honestly i dont see the point in living",
              "what's the point of being alive", "there's no point in going on"]:
        assert assess(t, [], None, screen=False)["risk"] >= 0.35, t
    for t in ["I don't see the point of this assignment", "no point in going to that lecture"]:
        assert assess(t, [], None, screen=False)["risk"] < 0.35, t


@pytest.mark.parametrize("text", [
    "I don’t want to be here anymore",          # iPhone curly apostrophe
    "I don’t see the point of being here anymore",
    "I wanna die",
    "thinking about jumping off the bridge tonight",
    "i’m going to end it",
    "I want to hang myself",
])
def test_rules_alone_catch_phone_typing_and_informal_language(text):
    from zenai.models.crisis import assess

    assert assess(text, [], None, screen=False)["risk"] >= 0.35, text


@pytest.mark.parametrize("text", [
    "this exam is killing me", "I’m dying to see the game tonight", "we jumped off the bus early",
    "I want to end this semester strong", "the bridge on campus is closed",
])
def test_ordinary_language_stays_clear(text):
    from zenai.models.crisis import assess

    assert assess(text, [], None, screen=False)["risk"] < 0.35, text
