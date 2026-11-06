"""Pilot requests from the For universities page.

These are business contacts a counselor or administrator typed in on purpose, so
they are kept as written (zenai.db.store.add_pilot_request). Nothing from any
student ever goes through here.
"""

from __future__ import annotations

import re

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from zenai.api import limits
from zenai.api.routes.auth import _db
from zenai.db import store

router = APIRouter(prefix="/pilot", tags=["pilot"])
EMAIL = re.compile(r"^[^@\s]{1,64}@([A-Za-z0-9-]+\.)+[A-Za-z]{2,}$")


class PilotIn(BaseModel):
    name: str = Field(..., min_length=2, max_length=120)
    email: str = Field(..., max_length=254)
    institution: str = Field(..., min_length=2, max_length=200)
    role: str = Field("", max_length=120)
    message: str = Field("", max_length=2000)
    website: str = Field("", max_length=200)      # left empty by people; bots fill it in


@router.post("")
def request_pilot(body: PilotIn, req: Request) -> dict:
    if body.website:
        return {"ok": True}                          # quietly drop bots
    if not EMAIL.match(body.email.strip()):
        raise HTTPException(422, {"message": "Please check the email address."})
    if not limits.allow(req, "tts"):
        raise HTTPException(429, {"message": "Thanks, we already have your request. Try again later if you need to."})
    try:
        with _db() as conn:
            store.add_pilot_request(conn, body.name.strip(), body.email.strip(), body.institution.strip(),
                                    body.role.strip(), body.message.strip())
    except HTTPException as e:
        if e.status_code != 503:
            raise
        raise HTTPException(503, {"message": "We couldn't save your request just now. Please try again in a few minutes."}) from e
    return {"ok": True}
