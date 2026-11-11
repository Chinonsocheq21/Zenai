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


# ---------- ACT values cues ----------
# "Direction, motivation, what's the point" -- a question, never a prescription,
# and never on crisis text (the crisis rail in agents/turn.py stops the turn
# before routing is even reached, so this never has a say over a crisis message).


def test_values_cue_on_a_plain_message_adds_an_invitation_not_a_prescription():
    r = route("I don't know, what's the point of any of this anymore")
    assert r["id"] is None  # no other specialist cue: stays the general Conversation Agent
    assert "values cue noticed" in r["why"]
    assert r["focus"] is not None
    assert "you may invite ONE values question" in r["focus"]
    assert "never as a suggestion or a plan" in r["focus"]
    for word in ("should", "try", "make sure"):
        assert word not in r["focus"].lower()


def test_values_cue_rides_on_top_of_a_matched_specialist():
    r = route("I have no motivation for my exams and midterms lately")
    assert r["id"] == "academic"
    assert "values cue noticed" in r["why"]
    assert "values question" in r["focus"]


def test_values_cue_does_not_ride_on_referral_which_already_asks_its_own_question():
    r = route("is there a tutor I can see for calc, I don't know what the point is")
    assert r["id"] == "referral"
    assert "values question" not in r["focus"]


def test_no_values_cue_leaves_focus_untouched():
    r = route("hey")
    assert r["id"] is None and r["focus"] is None


# ---------- exam season context ----------


def test_exam_season_context_only_reaches_the_academic_specialist():

    window = {"label": "Fall 2026 final exams", "start": "2026-12-11", "end": "2026-12-18"}
    r = route("I have two midterms Friday and my professor already said I'm failing", season=window)
    assert r["id"] == "academic"
    assert "Fall 2026 final exams" in r["focus"]
    assert "exam season (Fall 2026 final exams)" in r["why"]
    for word in ("should", "try", "make sure", "study tip"):
        assert word not in r["focus"].lower()
    # a different specialist, same season: no exam context added
    other = route("my chest is tight and I can't calm down", season=window)
    assert "Fall 2026" not in other["focus"]
    # no exam window today: no context added even for academic
    none_season = route("I have two midterms Friday and my professor already said I'm failing", season=None)
    assert "Fall 2026" not in none_season["focus"]


def test_exam_season_reads_campus_json_and_the_campus_own_timezone():
    import datetime as dt

    from zenai.agents import specialists

    # inside the real Fall 2026 final exams window (campuses.json)
    window = specialists.exam_season(now=dt.datetime(2026, 12, 15, 12, 0, tzinfo=dt.timezone.utc))
    assert window is not None and window["label"] == "Fall 2026 final exams"
    # well outside any window
    assert specialists.exam_season(now=dt.datetime(2026, 7, 4, 12, 0, tzinfo=dt.timezone.utc)) is None
