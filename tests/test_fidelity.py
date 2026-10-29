"""The drift detector on the film's own examples.

Skipped when the model isn't trained (CI has no ESConv); run locally after
`python -m training.train_drift`.
"""

import pytest

from zenai.models import fidelity

pytestmark = pytest.mark.skipif(not fidelity.available(), reason="drift detector not trained")


def test_the_films_drifting_reply_is_rejected_for_both_moves():
    r = fidelity.check("You've got this! Try breaking your notes into 25-minute blocks.")
    assert r["drift"] is True
    assert r["moves"]["advice"]["flagged"]
    assert r["moves"]["reassurance"]["flagged"]
    assert r["moves"]["advice"]["sentence"].startswith("Try breaking")


def test_the_films_in_protocol_reply_passes():
    r = fidelity.check("That opening-and-closing sounds exhausting on its own — separate from the "
                       "material. What happens in the moment just before you close it?")
    assert r["drift"] is False


def test_a_reflection_is_not_mistaken_for_reassurance():
    assert fidelity.check("It sounds like you've been carrying a lot on your own this week.")["drift"] is False


def test_diagnosis_is_reported_as_undetected_not_as_clear():
    d = fidelity.check("Sounds like test anxiety.")["moves"]["diagnosis"]
    assert d["score"] is None and "not detected" in d["status"]


def test_the_safe_fallback_passes_the_monitor_with_margin():
    """The fallback is what a student gets when every rewrite drifts. If our own
    detector would reject it, the loop has no safe exit."""
    from zenai.agents.conversation import SAFE_FALLBACK

    r = fidelity.check(SAFE_FALLBACK)
    assert r["drift"] is False
    for move in ("advice", "reassurance"):
        assert r["moves"][move]["score"] < r["moves"][move]["threshold"] - 0.15


# ---- the second opinion, with a stubbed judge (no model call) ----

def _stub_judge(monkeypatch, confirm: bool, diagnosis: bool = False, fail: bool = False):
    from zenai import llm
    from zenai.models import judge

    monkeypatch.setattr(llm, "available", lambda: True)

    def review(draft, suspects):
        if fail:   # the real review() fails closed; mimic its output
            return {"items": [{"id": s["id"], "confirmed": True} for s in suspects],
                    "diagnosis": {"present": False, "sentence": None}, "error": "down"}
        return {"items": [{"id": s["id"], "confirmed": confirm} for s in suspects],
                "diagnosis": {"present": diagnosis, "sentence": "Sounds like test anxiety." if diagnosis else None}}

    monkeypatch.setattr(judge, "review", review)


def test_second_opinion_can_overturn_a_false_flag(monkeypatch):
    _stub_judge(monkeypatch, confirm=False)
    r = fidelity.verify("You keep reaching for those notes and then shutting them right away.")
    assert r["drift"] is False and r["moves"]["advice"]["overturned"] is True


def test_second_opinion_failing_never_lets_drift_through(monkeypatch):
    _stub_judge(monkeypatch, confirm=False, fail=True)
    assert fidelity.verify("You've got this! Try breaking your notes into blocks.")["drift"] is True


def test_diagnosis_is_caught_by_the_second_opinion(monkeypatch):
    _stub_judge(monkeypatch, confirm=False, diagnosis=True)
    r = fidelity.verify("That sounds hard. Sounds like test anxiety.")
    assert r["moves"]["diagnosis"]["flagged"] is True and r["drift"] is True
