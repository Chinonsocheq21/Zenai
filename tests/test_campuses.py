"""The campus registry (zenai/campuses.json) and GET /campus."""

import copy
import json

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from zenai import campuses
from zenai.agents import resources


def _morgan():
    return copy.deepcopy(campuses.load()[0])


def _write(tmp_path, entries):
    p = tmp_path / "campuses.json"
    p.write_text(json.dumps({"campuses": entries}), encoding="utf-8")
    return p


def test_registry_loads_and_morgan_is_default():
    m = campuses.default()
    assert m["id"] == "morgan" and campuses.get("morgan") is m
    assert m["domains"] == ["morgan.edu"]
    assert m["timezone"] == "America/New_York"
    c = m["counseling"]
    assert c["phone"] == "443-885-3130" and c["line_24_7"] == "1-800-422-0009"
    assert (c["hours"]["opens"], c["hours"]["closes"]) == ("08:30", "17:00")
    assert campuses.by_domain("morgan.edu") is m
    assert campuses.by_domain("Student@MORGAN.edu") is m
    assert campuses.by_domain("gmail.com") is None and campuses.get("nope") is None


@pytest.mark.parametrize("breaks", [
    lambda c: c.pop("name"),
    lambda c: c.pop("domains"),
    lambda c: c.__setitem__("domains", ["Not A Domain"]),
    lambda c: c.__setitem__("timezone", "Eastern"),
    lambda c: c["counseling"].pop("line_24_7"),
    lambda c: c["counseling"].__setitem__("phone", "(443) 885 3130"),
    lambda c: c["counseling"].__setitem__("phone", "443-885-313"),
    lambda c: c["counseling"]["hours"].__setitem__("opens", "8:30am"),
    lambda c: c["resources"]["tutoring"].pop("url"),
    lambda c: c["resources"]["tutoring"].__setitem__("phone", "call CASA"),
    lambda c: c["resources"].pop("support"),
    lambda c: c.__setitem__("resources_verified", "Oct 2026"),
])
def test_validation_rejects_bad_entries(tmp_path, breaks):
    m = _morgan()
    breaks(m)
    with pytest.raises(campuses.CampusError):
        campuses.load(_write(tmp_path, [m]))


def test_duplicate_ids_and_domains_rejected(tmp_path):
    with pytest.raises(campuses.CampusError):
        campuses.load(_write(tmp_path, [_morgan(), _morgan()]))
    other = _morgan()
    other["id"] = "other"
    with pytest.raises(campuses.CampusError):
        campuses.load(_write(tmp_path, [_morgan(), other]))
    with pytest.raises(campuses.CampusError):
        campuses.load(_write(tmp_path, []))


def test_morgan_original_resources_unchanged():
    assert resources.VERIFIED == "2026-10-29"
    assert resources.cards(["counseling"])[0]["detail"] == "Weekdays 8:30 to 5 · 24/7 line: 1-800-422-0009"
    assert resources.cards(["counseling"])[0]["verified"] == "2026-10-29"
    assert [c["id"] for c in resources.cards(["unknown"])] == ["support"]
    tutoring = resources.RESOURCES["tutoring"]
    assert tutoring["name"] == "Center for Academic Success and Achievement (CASA)"
    assert tutoring["phone"] == "443-885-3380"


def test_new_morgan_offices_are_verified_from_morgan_edu():
    expected = {
        "financial_aid": ("443-885-3170", "https://www.morgan.edu/financialaid"),
        "health": ("443-885-3236", "https://www.morgan.edu/healthcenter"),
        "housing": ("443-885-3218", "https://www.morgan.edu/residencelife"),
        "title_ix": ("443-885-3580", "https://www.morgan.edu/titleix"),
        "career": ("443-885-3110", "https://www.morgan.edu/careerdevelopment"),
        "veterans": ("443-885-2046", "https://www.morgan.edu/veteranservices"),
        "international": ("443-885-4033", "https://www.morgan.edu/oisfs"),
    }
    for rid, (phone, url) in expected.items():
        r = resources.RESOURCES[rid]
        assert r["phone"] == phone
        assert r["url"] == url
        assert r["url"].startswith("https://www.morgan.edu/") or r["url"].startswith("https://morgan.edu/")
        assert r["verified"] == "2026-11-11"
        assert resources.cards([rid])[0]["id"] == rid


def test_keyword_matching_finds_the_right_office():
    assert resources.cards(["financial aid"])[0]["id"] == "financial_aid"
    assert resources.cards(["Housing"])[0]["id"] == "housing"
    assert resources.cards(["housing"])[0]["id"] == "housing"
    assert resources.cards(["unknown-topic"])[0]["id"] == "support"


def test_dean_of_students_care_team_is_the_sos_catch_all():
    support = resources.RESOURCES["support"]
    assert "CARE team" in support["what"]
    assert resources.cards(["support"])[0]["name"] == "Student Support and Outreach Services (S.O.S.)"


def test_exam_windows_present_and_sourced():
    m = campuses.default()
    assert m["exam_windows_source"] == "https://www.morgan.edu/academic-calendar"
    assert m["exam_windows_verified"] == "2026-11-11"
    labels = [w["label"] for w in m["exam_windows"]]
    assert "Fall 2026 final exams" in labels
    assert "Spring 2027 final exams" in labels
    fall_finals = next(w for w in m["exam_windows"] if w["label"] == "Fall 2026 final exams")
    assert (fall_finals["start"], fall_finals["end"]) == ("2026-12-11", "2026-12-18")
    spring_finals = next(w for w in m["exam_windows"] if w["label"] == "Spring 2027 final exams")
    assert (spring_finals["start"], spring_finals["end"]) == ("2027-05-08", "2027-05-14")


@pytest.mark.parametrize("breaks", [
    lambda c: c.__setitem__("exam_windows", []),
    lambda c: c.__setitem__("exam_windows", [{"label": "x", "start": "Dec 1 2026", "end": "2026-12-18"}]),
    lambda c: c.__setitem__("exam_windows", [{"label": "x", "start": "2026-12-18", "end": "2026-12-11"}]),
    lambda c: c.pop("exam_windows_source"),
    lambda c: c.__setitem__("exam_windows_verified", "soon"),
])
def test_exam_window_validation_rejects_bad_entries(tmp_path, breaks):
    m = _morgan()
    breaks(m)
    with pytest.raises(campuses.CampusError):
        campuses.load(_write(tmp_path, [m]))


def test_second_campus_is_one_json_entry(tmp_path, monkeypatch):
    two = _morgan()
    two.update(id="towson", name="Towson University", domains=["towson.edu"])
    two["counseling"].update(name="Towson Counseling Center", phone="410-704-2512")
    two["resources"] = {"support": {"name": "Dean of Students", "what": "Help sorting things out.",
                                    "phone": "410-704-2055", "detail": "Towson, MD",
                                    "url": "https://www.towson.edu/studentaffairs"}}
    path = _write(tmp_path, [_morgan(), two])
    monkeypatch.setattr(campuses, "PATH", path)
    campuses.all_campuses.cache_clear()
    try:
        assert campuses.default()["id"] == "morgan"
        assert campuses.by_domain("towson.edu")["id"] == "towson"
        cards = resources.cards(["tutoring"], campus_id="towson")
        assert [c["name"] for c in cards] == ["Dean of Students"]
        assert resources.cards(["tutoring"])[0]["name"].startswith("Center for Academic Success")
        body = _client().get("/campus", params={"id": "towson"}).json()
        assert body["counseling"]["phone"] == "410-704-2512"
    finally:
        campuses.all_campuses.cache_clear()


def _client():
    from zenai.api.routes import campus

    app = FastAPI()
    app.include_router(campus.router)
    return TestClient(app)


def test_campus_endpoint_returns_morgan_numbers():
    c = _client()
    for r in (c.get("/campus", params={"id": "morgan"}), c.get("/campus")):
        assert r.status_code == 200
        b = r.json()
        assert b["id"] == "morgan" and b["timezone"] == "America/New_York"
        assert b["counseling"]["name"] == "Morgan State University Counseling Center"
        assert b["counseling"]["phone"] == "443-885-3130"
        assert b["counseling"]["line_24_7"] == "1-800-422-0009"
        assert b["counseling"]["hours"]["label"] == "Weekdays 8:30 to 5"
        assert "domains" not in b
        # the resource finder and the client-side exam-season check both read GET
        # /campus, so public() carries the verified resource cards and exam windows
        assert any(r["id"] == "tutoring" and r["url"] == "https://www.morgan.edu/tutoring" for r in b["resources"])
        assert all({"name", "what", "phone", "url"} <= r.keys() for r in b["resources"])
        labels = [w["label"] for w in b["exam_windows"]]
        assert "Fall 2026 final exams" in labels
    assert c.get("/campus", params={"id": "nowhere"}).status_code == 404
