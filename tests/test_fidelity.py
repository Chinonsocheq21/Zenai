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
