"""Anonymous weekly trends for a campus in a pilot.

What is counted, per campus per week, from the real student app only:
  messages, new conversations, crisis hand-offs, the check-in level a
  conversation started with, and which focus (specialist) replied.
Never any text, never who, never a time finer than the week. Students who
aren't signed in count under "open".

GET /aggregate?weeks=8   header X-Pilot-Code -> the campus that code belongs to.
Any number under 10 is returned as null ("fewer than 10"), so a small group
can't be picked out.

Counting must never slow down or break chat: it runs after the reply is
ready, swallows every error, and skips the database for a minute after one.
"""

from __future__ import annotations

import os
import time
from datetime import date, datetime, timedelta, timezone

from fastapi import APIRouter, HTTPException, Request

from zenai.db import store

router = APIRouter(prefix="/aggregate", tags=["aggregate"])

MIN_GROUP = 10
CHECKINS = ["Light", "A bit much", "Heavy", "Very heavy", "I'm not okay"]
_down_until = 0.0
_ready = False


def week_of(d: date) -> date:
    return d - timedelta(days=d.weekday())          # Monday


def _metrics(body, out: dict) -> dict[str, int]:
    m = {"messages": 1}
    if not body.history:
        m["conversations"] = 1
        if body.checkin in CHECKINS:
            m[f"checkin:{CHECKINS.index(body.checkin)}"] = 1
    if out.get("escalate"):
        m["handoffs"] = 1
    spec = (out.get("specialist") or {}).get("id")
    if spec:
        m[f"focus:{spec}"] = 1
    return m


def record_turn(req: Request, body, out: dict) -> None:
    global _down_until, _ready
    if getattr(body, "client", "") != "student" or not isinstance(out, dict) or time.time() < _down_until:
        return
    try:
        with store.connect() as conn:
            if not _ready:
                store.migrate(conn)
                _ready = True
            u = store.user_for_session(conn, req.cookies.get("zenai_session"))
            store.bump(conn, week_of(datetime.now(timezone.utc).date()), u["campus"] if u else "open", _metrics(body, out))
    except Exception:  # noqa: BLE001 -- trends are optional; the reply is not
        _down_until = time.time() + 60


def pilot_codes() -> dict[str, str]:
    """PILOT_CODES="morgan.edu:long-random-code,other.edu:..." -> {code: campus}."""
    out = {}
    for pair in os.environ.get("PILOT_CODES", "").split(","):
        campus, _, code = pair.strip().partition(":")
        if campus and len(code) >= 16:
            out[code] = campus
    return out


@router.get("")
def trends(req: Request, weeks: int = 8) -> dict:
    campus = pilot_codes().get((req.headers.get("x-pilot-code") or "").strip())
    if not campus:
        raise HTTPException(401, {"message": "That pilot code isn't recognized."})
    weeks = max(1, min(weeks, 26))
    since = week_of(datetime.now(timezone.utc).date()) - timedelta(weeks=weeks - 1)
    try:
        with store.connect() as conn:
            store.migrate(conn)
            rows = store.weekly(conn, campus, since)
    except store.Unavailable as e:
        raise HTTPException(503, {"message": "Trends aren't available right now. Try again later."}) from e
    by: dict[str, dict[str, int]] = {}
    for w, m, n in rows:
        by.setdefault(w.isoformat(), {})[m] = n
    out = []
    for i in range(weeks):
        w = (since + timedelta(weeks=i)).isoformat()
        raw = by.get(w, {})
        out.append({"week": w, **{m: (n if n >= MIN_GROUP else None) for m, n in raw.items()}})
    return {"campus": campus, "min_group": MIN_GROUP, "weeks": out}
