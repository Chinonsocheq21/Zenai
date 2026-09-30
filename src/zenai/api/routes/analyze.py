"""The midterm demo endpoint.

Text in -> distress distribution and crisis risk out, with the escalation
decision. This is what gets clicked live on Oct 15, from /docs.

The ordering here is the safety design, and it is not negotiable:
PRIVACY -> CRISIS -> everything else. No therapy content is generated for a
turn that trips the crisis rail.
"""

from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel, Field

from zenai.config import settings

router = APIRouter(tags=["analyze"])


class AnalyzeIn(BaseModel):
    text: str = Field(..., min_length=1, max_length=4000)
    session_id: int | None = None


class AnalyzeOut(BaseModel):
    redacted_text: str
    distress: dict[str, float]
    primary_emotion: str
    crisis_risk: float
    escalate: bool
    escalation: dict | None = None
    note: str | None = None


@router.post("/analyze", response_model=AnalyzeOut)
def analyze(body: AnalyzeIn) -> AnalyzeOut:
    from zenai.agents.privacy import redact
    from zenai.models.crisis import score_risk
    from zenai.models.distress import classify

    redacted = redact(body.text)
    risk = score_risk(redacted)
    escalate = risk >= settings.CRISIS_THRESHOLD

    if escalate:
        return AnalyzeOut(
            redacted_text=redacted,
            distress={},
            primary_emotion="not_assessed",
            crisis_risk=risk,
            escalate=True,
            escalation={
                "hotline": settings.CRISIS_HOTLINE,
                "campus": settings.CAMPUS_COUNSELING_NAME,
                "phone": settings.CAMPUS_COUNSELING_PHONE or "NOT CONFIGURED",
                "action": "human_handoff",
            },
            note="Crisis rail tripped. No therapy content generated for this turn.",
        )

    dist = classify(redacted)
    return AnalyzeOut(
        redacted_text=redacted,
        distress=dist,
        primary_emotion=max(dist, key=dist.get) if dist else "unknown",
        crisis_risk=risk,
        escalate=False,
    )
