"""Pilot requests from the For universities page.

These are business contacts a counselor or administrator typed in on purpose, so
they are kept as written (zenai.db.store.add_pilot_request). Nothing from any
student ever goes through here.

A request must be impossible to lose:
  * It is stored, AND emailed privately to env NOTIFY_EMAIL through Resend
    (RESEND_API_KEY; sender MAIL_FROM, else Resend's test sender). The notify
    address is never hard-coded, logged or returned.
  * If the database is down but the notification went out, the requester is told
    it was received. Only when both fail do they see a calm "try again later".
  * The requester gets a short confirmation, best effort: with Resend's test
    sender only the account owner can receive mail, so a failed confirmation
    never fails the request. Every email has a 10 s timeout.
  * Pilot requests have their own rate-limit bucket (PER_HOUR per device per
    hour), counted here with the same Redis-or-memory approach as
    zenai.api.limits, rather than borrowing another bucket.
"""

from __future__ import annotations

import hashlib
import logging
import os
import re
import threading
import time
from collections import defaultdict, deque

import httpx
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from zenai.api import limits
from zenai.api.routes.auth import _db
from zenai.db import store

router = APIRouter(prefix="/pilot", tags=["pilot"])
EMAIL = re.compile(r"^[^@\s]{1,64}@([A-Za-z0-9-]+\.)+[A-Za-z]{2,}$")
RESEND = "https://api.resend.com/emails"
TIMEOUT = 10
PER_HOUR = 5                         # pilot requests per device per hour
WINDOW = 3600
OUTBOX: list[dict] = []              # local and tests without Resend: mail lands here
log = logging.getLogger("zenai.pilot")

_lock = threading.Lock()
_hits: dict[str, deque] = defaultdict(deque)


class PilotIn(BaseModel):
    name: str = Field(..., min_length=2, max_length=120)
    email: str = Field(..., max_length=254)
    institution: str = Field(..., min_length=2, max_length=200)
    role: str = Field("", max_length=120)
    message: str = Field("", max_length=2000)
    website: str = Field("", max_length=200)      # left empty by people; bots fill it in


# ---------------------------------------------------------------- rate limit

def _allow_redis(conn: tuple[str, str], dev: str, now: float) -> bool:
    url, tok = conn
    key = f"zl:pilot:{hashlib.sha256(dev.encode()).hexdigest()[:24]}:{int(now // WINDOW)}"
    auth = {"Authorization": f"Bearer {tok}"}
    r = httpx.post(f"{url}/pipeline", json=[["GET", key]], headers=auth, timeout=1.5)
    r.raise_for_status()
    if int(r.json()[0]["result"] or 0) >= PER_HOUR:
        return False
    r = httpx.post(f"{url}/pipeline", json=[["INCR", key], ["EXPIRE", key, str(WINDOW + 60)]],
                   headers=auth, timeout=1.5)
    r.raise_for_status()
    return True


def allow(req: Request) -> bool:
    """True if this device may send one more pilot request this hour (and count it)."""
    now, dev = time.time(), limits.device(req)
    conn = limits._redis()
    if conn:
        try:
            return _allow_redis(conn, dev, now)
        except (httpx.HTTPError, ValueError, KeyError, TypeError, IndexError) as e:
            log.warning("pilot limit: Redis unavailable (%s), counting in memory", type(e).__name__)
    with _lock:
        q = _hits[dev]
        while q and now - q[0] > WINDOW:
            q.popleft()
        if len(q) >= PER_HOUR:
            return False
        q.append(now)
        return True


def reset() -> None:
    with _lock:
        _hits.clear()
    OUTBOX.clear()


# ---------------------------------------------------------------- email

def _mail(to: str, subject: str, text: str, reply_to: str | None = None) -> bool:
    """Send one email through Resend. True only if the provider accepted it.
    Best effort: never raises, never logs addresses or content."""
    key = os.environ.get("RESEND_API_KEY")
    if not key:
        if not os.environ.get("VERCEL"):
            OUTBOX.append({"to": to, "subject": subject, "text": text})
        return False
    payload = {"from": os.environ.get("MAIL_FROM") or "ZenAI <onboarding@resend.dev>",
               "to": [to], "subject": subject, "text": text}
    if reply_to:
        payload["reply_to"] = reply_to
    try:
        r = httpx.post(RESEND, timeout=TIMEOUT, headers={"Authorization": f"Bearer {key}"}, json=payload)
    except Exception as e:  # noqa: BLE001 -- email is best effort
        log.warning("pilot email: send failed (%s)", type(e).__name__)
        return False
    if r.status_code >= 400:
        log.warning("pilot email: provider refused (%s)", r.status_code)
        return False
    return True


def _notify(b: PilotIn, stored: bool) -> bool:
    to = os.environ.get("NOTIFY_EMAIL", "").strip()
    if not to:
        return False
    note = "" if stored else "\n\nThe database was unavailable, so this request is ONLY in this email.\n"
    text = (f"New pilot request from the For universities page.{note}\n\n"
            f"Name: {b.name}\nInstitution: {b.institution}\nRole: {b.role or '(not given)'}\n"
            f"Email: {b.email}\n\nMessage:\n{b.message or '(none)'}\n")
    return _mail(to, f"Pilot request: {b.institution}", text, reply_to=b.email)


def _confirm(b: PilotIn) -> None:
    text = (f"Hi {b.name},\n\nThanks for asking about a ZenAI pilot for {b.institution}. "
            "We have your request and will reply within two business days to this address.\n\nZenAI")
    _mail(b.email, "We received your ZenAI pilot request", text)


# ---------------------------------------------------------------- route

@router.post("")
def request_pilot(body: PilotIn, req: Request) -> dict:
    if body.website:
        return {"ok": True}                          # quietly drop bots
    body = PilotIn(name=body.name.strip(), email=body.email.strip(), institution=body.institution.strip(),
                   role=body.role.strip(), message=body.message.strip())
    if not EMAIL.match(body.email):
        raise HTTPException(422, {"message": "Please check the email address."})
    if not allow(req):
        raise HTTPException(429, {"message": "Thanks, we already have your request. Try again later if you need to."})
    stored = False
    try:
        with _db() as conn:
            store.add_pilot_request(conn, body.name, body.email, body.institution, body.role, body.message)
        stored = True
    except HTTPException as e:
        if e.status_code != 503:
            raise
    except store.Unavailable:
        pass
    notified = _notify(body, stored)
    if not stored and not notified:
        raise HTTPException(503, {"message": "We couldn't save your request just now. Please try again later."})
    _confirm(body)
    return {"ok": True}
