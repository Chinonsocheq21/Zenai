"""The crisis check reads the conversation, and context only ever raises risk."""

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
