"""The Resource & Referral specialist's verified cards (zenai/agents/resources.py)."""

from zenai.agents import resources


def test_cards_preserves_original_four_plus_catch_all():
    for rid in ("counseling", "tutoring", "disability", "basic_needs", "support"):
        assert rid in resources.RESOURCES


def test_cards_adds_the_wider_morgan_offices():
    for rid in ("financial_aid", "health", "housing", "title_ix", "career", "veterans", "international"):
        assert rid in resources.RESOURCES
        r = resources.RESOURCES[rid]
        for field in ("name", "what", "phone", "detail", "url"):
            assert r.get(field), f"{rid} missing {field}"
        assert r["url"].startswith("https://www.morgan.edu/") or r["url"].startswith("https://morgan.edu/")


def test_cards_returns_requested_topics_in_order_deduped():
    out = resources.cards(["housing", "counseling", "housing"])
    assert [c["id"] for c in out] == ["housing", "counseling"]


def test_cards_falls_back_to_support_for_unknown_topics():
    out = resources.cards(["not-a-real-topic"])
    assert [c["id"] for c in out] == ["support"]


def test_cards_matches_loose_phrases_to_the_right_office():
    assert resources.cards(["financial aid"])[0]["id"] == "financial_aid"
    assert resources.cards(["Financial Aid"])[0]["id"] == "financial_aid"
    assert resources.cards(["housing"])[0]["id"] == "housing"
    assert resources.cards(["Housing"])[0]["id"] == "housing"
    assert resources.cards(["title ix"])[0]["id"] == "title_ix"
    assert resources.cards(["veterans"])[0]["id"] == "veterans"
    assert resources.cards(["international"])[0]["id"] == "international"
    assert resources.cards(["career"])[0]["id"] == "career"
    assert resources.cards(["health"])[0]["id"] == "health"


def test_each_card_carries_its_own_verified_date_when_set():
    card = resources.cards(["financial_aid"])[0]
    assert card["verified"] == "2026-11-11"
    old_card = resources.cards(["counseling"])[0]
    assert old_card["verified"] == "2026-10-29"


def test_no_card_is_missing_a_phone_or_url():
    for rid in resources.RESOURCES:
        out = resources.cards([rid])[0]
        assert out["phone"]
        assert out["url"]
