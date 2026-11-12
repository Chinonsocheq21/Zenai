"""Anonymous weekly trends for a campus in a pilot.

What is counted, per campus per week, from the real student app only:
  messages, new conversations, crisis hand-offs (and which layer caught
  each one: patterns on the message itself, patterns escalated by earlier
  context, or the model screen), the check-in level a conversation started
  with, which focus (specialist) replied, whether the reply was checked by
  the Fidelity Monitor, whether the first draft passed, whether a draft was
  rejected and rewritten, whether the safe fallback was used, whether the
  message arrived while the campus counseling office was closed, how fast
  the whole turn was (fast under 3 s, ok 3 to 8 s, slow over 8 s), and
  whether the turn came from a signed-in session.
Never any text, never who, never a time finer than the week. Students who
aren't signed in count under "open".

GET /aggregate?weeks=8   header X-Pilot-Code -> the campus that code belongs to.
GET /aggregate/demo      the same shape, no code needed, with clearly synthetic
data for a campus called "demo", so the dashboard can be shown without a pilot.
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

_DAY_ABBR = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]


def _now() -> datetime:
    """The clock record_turn and the endpoints use -- its own function so a
    test can hold it still instead of depending on when the suite happens to run."""
    return datetime.now(timezone.utc)


def week_of(d: date) -> date:
    return d - timedelta(days=d.weekday())          # Monday


def _parse_clock(s: str) -> int:
    h, m = s.split(":")
    return int(h) * 60 + int(m)


def _days_open(spec: str) -> set[int]:
    """"Mon-Fri" or "Mon,Wed,Fri" -> {0, 1, 2, 3, 4} (Monday = 0, as in
    datetime.weekday()). Unknown abbreviations are ignored, never raise."""
    out: set[int] = set()
    for part in (spec or "").split(","):
        part = part.strip()
        if not part:
            continue
        a, _, b = part.partition("-")
        try:
            ai = _DAY_ABBR.index(a.strip()[:3].title())
        except ValueError:
            continue
        if not b:
            out.add(ai)
            continue
        try:
            bi = _DAY_ABBR.index(b.strip()[:3].title())
        except ValueError:
            continue
        i = ai
        while True:
            out.add(i)
            if i == bi:
                break
            i = (i + 1) % 7
    return out


def after_hours(campus: dict | None, now_utc: datetime) -> bool:
    """True when `now_utc` falls outside this campus counseling office's
    published hours (campuses.json), read in the campus's own timezone --
    the same logic as index.html's officeState(), in Python. Best-effort: a
    missing or malformed campus/hours entry counts as open, so a data problem
    never inflates "after hours"."""
    if not campus:
        return False
    try:
        from zoneinfo import ZoneInfo

        hours = campus["counseling"]["hours"]
        local = now_utc.astimezone(ZoneInfo(campus["timezone"]))
        if local.weekday() not in _days_open(hours["days"]):
            return True
        mins = local.hour * 60 + local.minute
        return not (_parse_clock(hours["opens"]) <= mins < _parse_clock(hours["closes"]))
    except Exception:  # noqa: BLE001 -- a malformed campus entry must never count as "after hours"
        return False


def _speed_bucket(ms: float | None) -> str | None:
    if ms is None:
        return None
    if ms < 3000:
        return "fast"
    if ms <= 8000:
        return "ok"
    return "slow"


def _metrics(body, out: dict, elapsed_ms: float | None, handoff_by: str | None,
             signed_in: bool, campus: dict | None, now: datetime) -> dict[str, int]:
    m = {"messages": 1}
    if not body.history:
        m["conversations"] = 1
        if body.checkin in CHECKINS:
            m[f"checkin:{CHECKINS.index(body.checkin)}"] = 1
    if out.get("escalate"):
        m["handoffs"] = 1
        if handoff_by in ("patterns", "context", "screen"):
            m[f"handoff_by:{handoff_by}"] = 1
    spec = (out.get("specialist") or {}).get("id")
    if spec:
        m[f"focus:{spec}"] = 1

    attempts = out.get("attempts") or []
    if any(a.get("checked") for a in attempts):
        m["checked"] = 1
        if any(a.get("drift") for a in attempts):
            m["rewritten"] = 1
        elif len(attempts) == 1 and not out.get("fallback"):
            m["first_pass"] = 1
    if out.get("fallback"):
        m["fallback"] = 1

    if after_hours(campus, now):
        m["after_hours"] = 1
    bucket = _speed_bucket(elapsed_ms)
    if bucket:
        m[f"speed:{bucket}"] = 1
    if signed_in:
        m["signed_in"] = 1
    return m


def record_turn(req: Request, body, out: dict, elapsed_ms: float | None = None,
                 handoff_by: str | None = None) -> None:
    global _down_until, _ready
    if getattr(body, "client", "") != "student" or not isinstance(out, dict) or time.time() < _down_until:
        return
    try:
        with store.connect() as conn:
            if not _ready:
                store.migrate(conn)
                _ready = True
            u = store.user_for_session(conn, req.cookies.get("zenai_session"))
            campus = None
            if u:
                from zenai import campuses

                campus = campuses.by_domain(u["campus"])
            now = _now()
            metrics = _metrics(body, out, elapsed_ms, handoff_by, signed_in=bool(u), campus=campus, now=now)
            store.bump(conn, week_of(now.date()), u["campus"] if u else "open", metrics)
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
    since = week_of(_now().date()) - timedelta(weeks=weeks - 1)
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


DEMO_WEEKS = 12
# A believable term: a quiet start, a midterm bump, a dip, then finals climbing.
_DEMO_CONVERSATIONS = (78, 86, 81, 97, 112, 104, 91, 88, 99, 108, 121, 116)
_DEMO_HANDOFFS = (4, 6, 5, 9, 12, 8, 6, 5, 7, 11, 13, 9)


def _demo_week(i: int) -> dict[str, int]:
    """One deterministic, clearly synthetic week of demo data (no randomness,
    no clock finer than "which week of the 12"), so /aggregate/demo always
    answers the same shape without touching the database. The numbers hang
    together the way real ones do: replies checked = messages minus hand-offs,
    check-ins add up to conversations, and some small counts fall under 10 so
    the dashboard shows how hidden groups look."""
    conversations = _DEMO_CONVERSATIONS[i % len(_DEMO_CONVERSATIONS)]
    messages = round(conversations * (2.9 + (i % 4) * 0.15))
    handoffs = _DEMO_HANDOFFS[i % len(_DEMO_HANDOFFS)]   # often under 10, sometimes not
    by_patterns = round(handoffs * 0.6)
    by_context = round(handoffs * 0.25)
    by_screen = max(0, handoffs - by_patterns - by_context)
    checked = messages - handoffs
    rewritten = 11 + (i * 3) % 9
    fallback = 1 + i % 3                            # always under 10
    first_pass = checked - rewritten
    speed_fast = round(checked * 0.62)
    speed_ok = round(checked * 0.31)
    speed_slow = checked - speed_fast - speed_ok

    m = {
        "messages": messages, "conversations": conversations, "handoffs": handoffs,
        "handoff_by:patterns": by_patterns, "handoff_by:context": by_context, "handoff_by:screen": by_screen,
        "checked": checked, "first_pass": first_pass, "rewritten": rewritten, "fallback": fallback,
        "after_hours": round(messages * (0.30 + (i % 4) * 0.03)), "signed_in": round(messages * 0.72),
        "speed:fast": speed_fast, "speed:ok": speed_ok, "speed:slow": speed_slow,
    }
    left = conversations
    for k, share in enumerate((0.30, 0.31, 0.22, 0.11)):
        m[f"checkin:{k}"] = round(conversations * share)
        left -= m[f"checkin:{k}"]
    m[f"checkin:{len(CHECKINS) - 1}"] = max(0, left)  # "I'm not okay": the remainder, usually under 10
    for sid, share in (("academic", 0.45), ("stress_relief", 0.25), ("wellness", 0.2), ("referral", 0.1)):
        m[f"focus:{sid}"] = round(checked * share)
    return m


@router.get("/demo")
def demo() -> dict:
    """The same shape as GET /aggregate, no pilot code needed: deterministic,
    clearly synthetic data for campus "demo", so a director can see the
    dashboard (/dashboard/?demo=1) without one."""
    since = week_of(_now().date()) - timedelta(weeks=DEMO_WEEKS - 1)
    weeks = []
    for i in range(DEMO_WEEKS):
        w = (since + timedelta(weeks=i)).isoformat()
        raw = _demo_week(i)
        weeks.append({"week": w, **{m: (n if n >= MIN_GROUP else None) for m, n in raw.items()}})
    return {"campus": "demo", "min_group": MIN_GROUP, "weeks": weeks, "demo": True}
