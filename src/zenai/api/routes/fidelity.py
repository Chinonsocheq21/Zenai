"""Check a candidate reply for drift, the way the Fidelity Monitor will before
every reply is sent. Until the Conversation Agent exists to write drafts, a
person supplies the draft -- which is also how the detector gets demoed and
audited."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

router = APIRouter(tags=["fidelity"])


class DraftIn(BaseModel):
    reply: str = Field(..., min_length=1, max_length=4000)


@router.post("/fidelity/check")
def fidelity_check(body: DraftIn) -> dict:
    from zenai.models import fidelity

    if not fidelity.available():
        raise HTTPException(503, "Drift detector not trained. Run: python -m training.train_drift")
    return fidelity.check(body.reply)
