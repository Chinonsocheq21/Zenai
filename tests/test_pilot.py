"""Pilot requests: stored as written, bots dropped, calm when the database is down."""

from fastapi.testclient import TestClient

from zenai.api import limits
from zenai.api.main import app

OK = {"name": "Dr. Ada Lane", "email": "ada.lane@example.edu", "institution": "Example State University",
      "role": "Counseling Center Director", "message": "Interested in a spring pilot."}


def test_request_is_stored(pg):
    limits.reset()
    assert TestClient(app).post("/pilot", json=OK).json() == {"ok": True}
    row = pg.execute("SELECT name, email, institution, role, message FROM pilot_requests").fetchone()
    assert row == (OK["name"], OK["email"], OK["institution"], OK["role"], OK["message"])


def test_bots_and_bad_input(pg):
    limits.reset()
    c = TestClient(app)
    assert c.post("/pilot", json={**OK, "website": "http://spam"}).json() == {"ok": True}
    assert pg.execute("SELECT count(*) FROM pilot_requests").fetchone()[0] == 0
    assert c.post("/pilot", json={**OK, "email": "nope"}).status_code == 422
    assert c.post("/pilot", json={**OK, "name": ""}).status_code == 422


def test_database_down_is_calm():
    limits.reset()
    r = TestClient(app).post("/pilot", json=OK)
    assert r.status_code == 503 and "try again" in r.json()["detail"]["message"]
