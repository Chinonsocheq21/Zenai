"""The campus registry: every campus ZenAI serves, as data in campuses.json.

A campus is its name, sign-in domains, counseling center (office phone, hours,
24/7 line) and the verified resource cards the Resource & Referral specialist
shows. Adding a campus is one entry in campuses.json; no code changes.

The file is read once and validated on first use. A malformed entry raises
CampusError instead of serving a wrong phone number.
"""

from __future__ import annotations

import json
import re
from functools import lru_cache
from pathlib import Path

PATH = Path(__file__).with_name("campuses.json")

PHONE = re.compile(r"^(1-)?\d{3}-\d{3}-\d{4}$")
DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
CLOCK = re.compile(r"^([01]\d|2[0-3]):[0-5]\d$")
TIMEZONE = re.compile(r"^[A-Za-z_]+(/[A-Za-z0-9_+-]+)+$")
DOMAIN = re.compile(r"^[a-z0-9-]+(\.[a-z0-9-]+)+$")
RESOURCE_FIELDS = ("name", "what", "phone", "detail", "url")


class CampusError(ValueError):
    """campuses.json has an entry that is missing or malformed."""


def _need(obj: dict, key: str, where: str):
    v = obj.get(key) if isinstance(obj, dict) else None
    if v in (None, "", [], {}):
        raise CampusError(f"{where}: missing {key!r}")
    return v


def _phone(v, where: str) -> None:
    if not isinstance(v, str) or not PHONE.match(v):
        raise CampusError(f"{where}: phone {v!r} is not like 443-885-3130 or 1-800-422-0009")


def validate(campus: dict) -> dict:
    """Check one campus entry; return it unchanged or raise CampusError."""
    cid = _need(campus, "id", "campus")
    w = f"campus {cid!r}"
    if not isinstance(cid, str) or not re.match(r"^[a-z0-9_-]+$", cid):
        raise CampusError(f"{w}: id must be lowercase letters, digits, - or _")
    _need(campus, "name", w)
    domains = _need(campus, "domains", w)
    if not isinstance(domains, list) or not all(isinstance(d, str) and DOMAIN.match(d) for d in domains):
        raise CampusError(f"{w}: domains must be a list of lowercase domains like 'morgan.edu'")
    tz = _need(campus, "timezone", w)
    if not isinstance(tz, str) or not TIMEZONE.match(tz):
        raise CampusError(f"{w}: timezone {tz!r} is not an IANA name like 'America/New_York'")

    c = _need(campus, "counseling", w)
    cw = f"{w} counseling"
    _need(c, "name", cw)
    _phone(_need(c, "phone", cw), cw)
    _phone(_need(c, "line_24_7", cw), cw + " line_24_7")
    _need(c, "url", cw)
    h = _need(c, "hours", cw)
    for k in ("days", "opens", "closes", "label"):
        _need(h, k, cw + " hours")
    if not CLOCK.match(str(h["opens"])) or not CLOCK.match(str(h["closes"])):
        raise CampusError(f"{cw} hours: opens/closes must be HH:MM (24-hour)")

    verified = _need(campus, "resources_verified", w)
    if not DATE.match(str(verified)):
        raise CampusError(f"{w}: resources_verified must be YYYY-MM-DD")
    res = _need(campus, "resources", w)
    if "support" not in res:
        raise CampusError(f"{w}: resources needs a 'support' entry (the catch-all card)")
    for rid, r in res.items():
        rw = f"{w} resource {rid!r}"
        for k in RESOURCE_FIELDS:
            _need(r, k, rw)
        _phone(r["phone"], rw)
        if "verified" in r and not DATE.match(str(r["verified"])):
            raise CampusError(f"{rw}: verified must be YYYY-MM-DD")

    if "exam_windows" in campus:
        windows = campus["exam_windows"]
        ew = f"{w} exam_windows"
        if not isinstance(windows, list) or not windows:
            raise CampusError(f"{ew}: must be a non-empty list")
        _need(campus, "exam_windows_source", w)
        exam_verified = _need(campus, "exam_windows_verified", w)
        if not DATE.match(str(exam_verified)):
            raise CampusError(f"{w}: exam_windows_verified must be YYYY-MM-DD")
        for win in windows:
            ww = f"{ew} {win.get('label') if isinstance(win, dict) else win!r}"
            for k in ("label", "start", "end"):
                _need(win, k, ww)
            if not DATE.match(str(win["start"])) or not DATE.match(str(win["end"])):
                raise CampusError(f"{ww}: start/end must be YYYY-MM-DD")
            if str(win["start"]) > str(win["end"]):
                raise CampusError(f"{ww}: start must not be after end")
    return campus


def load(path: Path | None = None) -> list[dict]:
    """Read and validate a registry file. The first campus is the default."""
    data = json.loads(Path(path or PATH).read_text(encoding="utf-8"))
    campuses = data.get("campuses") if isinstance(data, dict) else None
    if not campuses:
        raise CampusError("no campuses in the registry")
    seen_ids, seen_domains = set(), set()
    for c in campuses:
        validate(c)
        if c["id"] in seen_ids:
            raise CampusError(f"campus id {c['id']!r} appears twice")
        seen_ids.add(c["id"])
        for d in c["domains"]:
            if d in seen_domains:
                raise CampusError(f"domain {d!r} belongs to two campuses")
            seen_domains.add(d)
    return campuses


@lru_cache(maxsize=1)
def all_campuses() -> tuple:
    return tuple(load())


def default() -> dict:
    """The campus used when none is named: Morgan State, the first entry."""
    return all_campuses()[0]


def get(campus_id: str) -> dict | None:
    """The campus with this id, or None."""
    return next((c for c in all_campuses() if c["id"] == campus_id), None)


def by_domain(email_domain: str) -> dict | None:
    """The campus that signs in with this domain (or full email address), or None."""
    d = (email_domain or "").strip().lower().rsplit("@", 1)[-1]
    return next((c for c in all_campuses() if d in c["domains"]), None)


def public(campus: dict) -> dict:
    """The student-facing part: names, numbers, hours, 24/7 line, timezone."""
    c = campus["counseling"]
    return {
        "id": campus["id"],
        "name": campus["name"],
        "timezone": campus["timezone"],
        "counseling": {
            "name": c["name"],
            "phone": c["phone"],
            "hours": dict(c["hours"]),
            "line_24_7": c["line_24_7"],
            "url": c["url"],
        },
    }
