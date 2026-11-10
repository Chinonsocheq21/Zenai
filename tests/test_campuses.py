"""The campus registry (zenai/campuses.json) and GET /campus."""

import copy
import hashlib
import json

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from zenai import campuses
from zenai.agents import resources

# sha256 of the resources output BEFORE they moved into the registry (ZL-32):
# json.dumps({VERIFIED, RESOURCES, cards(all topics), cards([])}, sort_keys=True).
BEFORE_SHA256 = "c46697e0571b49a77d13d741f38ed27a99211970fb7caa9eb9ff7b2b3cb84d64"


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


def test_morgan_resources_unchanged_byte_for_byte():
    out = json.dumps({"VERIFIED": resources.VERIFIED, "RESOURCES": resources.RESOURCES,
                      "cards": resources.cards(list(resources.RESOURCES)),
                      "none": resources.cards([])}, sort_keys=True)
    assert hashlib.sha256(out.encode()).hexdigest() == BEFORE_SHA256
    assert resources.VERIFIED == "2026-10-29"
    assert resources.cards(["counseling"])[0]["detail"] == "Weekdays 8:30 to 5 · 24/7 line: 1-800-422-0009"
    assert [c["id"] for c in resources.cards(["unknown"])] == ["support"]


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
        assert "resources" not in b and "domains" not in b
    assert c.get("/campus", params={"id": "nowhere"}).status_code == 404
