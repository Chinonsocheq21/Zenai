from training.taxonomy import map_goemotions
from zenai.agents.privacy import redact
from zenai.models.crisis import score_risk


def test_distress_outranks_neutral():
    assert map_goemotions(["nervousness", "joy"]) == "anxiety"


def test_priority_order():
    assert map_goemotions(["fear", "sadness"]) == "anxiety"


def test_unmapped_is_neutral():
    assert map_goemotions(["admiration"]) == "neutral_or_positive"


def test_redaction():
    out = redact("mail me chege4@morgan.edu or 443-555-0182, id 12345678")
    assert "@morgan.edu" not in out and "443" not in out and "12345678" not in out


def test_crisis_lexicon_is_paranoid():
    assert score_risk("i want to die") > 0.9
    assert score_risk("i feel hopeless") > 0.5
    assert score_risk("i have three exams") < 0.1


def test_crisis_catches_paraphrases():
    """Regression: the first lexicon matched fixed phrases and missed these.

    Found by training/eval_crisis.py on its first run. A crisis detector that
    misses an obvious rewording of the thing it exists to catch looks like it
    is working when it is not, so these are pinned.
    """
    for text in [
        "I have been thinking about hurting myself",   # was: only "hurt myself"
        "I do not see any way out of this",            # was: only "no way out"
        "nothing is worth living for right now",       # was: only "not worth living"
        "everyone would be better off without me",
        "I don't want to be here anymore",
    ]:
        assert score_risk(text) >= 0.35, text


def test_crisis_does_not_fire_on_ordinary_stress():
    for text in [
        "I have three exams this week and I cannot sleep",
        "my roommate situation is stressing me out",
        "how do I book an appointment with an advisor",
    ]:
        assert score_risk(text) < 0.35, text
