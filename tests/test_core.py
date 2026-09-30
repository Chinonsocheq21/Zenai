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
