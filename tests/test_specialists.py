"""The router: right specialist, explainable, and never a second protocol."""

from zenai.agents import conversation, resources
from zenai.agents.specialists import SPECIALISTS
from zenai.agents.specialists import route_rules as route


def test_academic():
    r = route("I have two midterms Friday and my professor already said I'm failing")
    assert r["id"] == "academic" and "midterms" in r["why"]


def test_stress_relief_and_mood_tiebreak():
    assert route("my chest is tight and I can't calm down")["id"] == "stress_relief"
    r = route("I'm tired and nervous", mood="anxiety")
    assert r["id"] == "stress_relief" and "tie broken by mood" in r["why"]


def test_wellness():
    assert route("I've pulled two all-nighters and keep skipping meals")["id"] == "wellness"


def test_referral_needs_an_ask():
    r = route("is there a tutor I can see for calc?")
    assert r["id"] == "referral" and r["resources"] == ["tutoring"]
    # mentioning food is not asking for food help
    assert route("I ate food at the dining hall and felt sick about the exam")["id"] != "referral"


def test_referral_cards_are_curated():
    c = resources.cards(["counseling", "nonsense"])
    assert [x["id"] for x in c] == ["counseling"] and c[0]["phone"] == "443-885-3130"
    assert resources.cards([])[0]["id"] == "support"


def test_general_when_no_cue():
    assert route("hey")["id"] is None


def test_focus_never_replaces_protocol():
    for s in SPECIALISTS.values():
        msgs = conversation.build_messages("hi", focus=s["focus"])
        assert msgs[0]["content"].startswith(conversation.PROTOCOL_V0)
        assert "FOCUS FOR THIS MESSAGE" in msgs[0]["content"]


def test_model_route_falls_back_to_rules(monkeypatch):
    from zenai import llm
    from zenai.agents import specialists

    monkeypatch.setattr(llm, "available", lambda: True)

    def boom(*a, **k):
        raise llm.LLMError("down")
    monkeypatch.setattr(llm, "chat", boom)
    r = specialists.route("two midterms friday")
    assert r["by"] == "rules" and r["id"] == "academic"


def test_model_route_parses(monkeypatch):
    from zenai import llm
    from zenai.agents import specialists

    monkeypatch.setattr(llm, "available", lambda: True)
    monkeypatch.setattr(llm, "chat", lambda *a, **k: {"text": '{"label":"referral","topics":["tutoring"],"why":"asks for tutor"}', "ms": 5})
    r = specialists.route("anyone help with calc?")
    assert r["id"] == "referral" and r["resources"] == ["tutoring"] and r["by"] == "model"
