"""Check-ins that follow a signed-in student between devices, only if they
turned syncing on. A check-in is a day and a level (0 Light .. 3 Very heavy);
nothing a student types is ever part of it.

GET  /checkins?days=90         -> {sync, checkins: [{day, level}]}
PUT  /checkins {day, level}    -> {stored}   (stored only while sync is on)
POST /checkins/sync {on, checkins?} -> turn sync on (optionally uploading this
                                device's history) or off (deletes what was synced)
"""

from __future__ import annotations

from datetime import date, datetime, timedelta, timezone

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from zenai.api.routes.auth import COOKIE, _db
from zenai.db import store

router = APIRouter(prefix="/checkins", tags=["checkins"])


class CheckinIn(BaseModel):
    day: date
    level: int = Field(..., ge=0, le=3)      # 4 ("I'm not okay") is a hand-off, never a stored check-in


class SyncIn(BaseModel):
    on: bool
    checkins: list[CheckinIn] = Field(default_factory=list, max_length=400)


def _user(conn, req: Request) -> dict:
    u = store.user_for_session(conn, req.cookies.get(COOKIE))
    if not u:
        raise HTTPException(401, {"message": "Sign in to sync check-ins."})
    return u


def _sane(d: date) -> bool:
    today = datetime.now(timezone.utc).date()
    return today - timedelta(days=400) <= d <= today + timedelta(days=1)


@router.get("")
def list_checkins(req: Request, days: int = 90) -> dict:
    with _db() as conn:
        u = _user(conn, req)
        since = datetime.now(timezone.utc).date() - timedelta(days=max(1, min(days, 400)))
        return {"sync": u["sync_checkins"], "checkins": store.checkins(conn, u["id"], since) if u["sync_checkins"] else []}


@router.put("")
def put_checkin(body: CheckinIn, req: Request) -> dict:
    if not _sane(body.day):
        raise HTTPException(422, {"message": "That date is out of range."})
    with _db() as conn:
        u = _user(conn, req)
        return {"stored": store.put_checkin(conn, u["id"], body.day, body.level)}


@router.post("/sync")
def set_sync(body: SyncIn, req: Request) -> dict:
    with _db() as conn:
        u = _user(conn, req)
        store.set_sync(conn, u["id"], body.on)
        uploaded = 0
        if body.on:
            for c in body.checkins:
                if _sane(c.day) and store.put_checkin(conn, u["id"], c.day, c.level):
                    uploaded += 1
        return {"sync": body.on, "uploaded": uploaded}
