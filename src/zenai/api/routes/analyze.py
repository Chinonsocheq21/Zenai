"""The turn endpoint the console and the demo use.

Text in -> what each stage of the pipeline did, out. The ordering is the safety
design and it is not negotiable:

    PRIVACY -> CRISIS -> everything else

No therapy content is generated for a turn that trips the crisis rail.

`trace` reports every stage of the turn, including the ones that are not built
yet, marked "pending". The console draws exactly this list, so it can never show
a stage running that does not run.
"""

from __future__ import annotations

import re
import time

from fastapi import APIRouter
from pydantic import BaseModel, Field

from zenai.config import settings

router = APIRouter(tags=["analyze"])

# The seven stages of a turn, in order. Keep in step with the architecture.
STAGES = ["privacy", "crisis", "mood", "memory", "conversation", "fidelity", "send"]
NOT_BUILT = {
    "memory": "Memory & Personalization — designed, not built yet",
    "conversation": "Conversation Agent (ACT/CBT) — needs a language model; scheduled Oct 22",
    "fidelity": "drift detector trained — no draft to check until the Conversation Agent exists (see the Fidelity Monitor tab)",
}


class AnalyzeIn(BaseModel):
    text: str = Field(..., min_length=1, max_length=4000)
    session_id: int | None = None


class Stage(BaseModel):
    stage: str
    status: str  # done | skipped | pending | escalated
    ms: float | None = None
    detail: str = ""


class AnalyzeOut(BaseModel):
    redacted_text: str
    distress: dict[str, float]
    primary_emotion: str
    crisis_risk: float
    escalate: bool
    escalation: dict | None = None
    note: str | None = None
    distress_model: str | None = None
    trace: list[Stage] = []


def _ms(t0: float) -> float:
    return round((time.perf_counter() - t0) * 1000, 2)


@router.post("/analyze", response_model=AnalyzeOut)
def analyze(body: AnalyzeIn) -> AnalyzeOut:
    from zenai.agents.privacy import redact
    from zenai.models.crisis import score_risk
    from zenai.models.distress import classify, which

    trace: list[Stage] = []

    t = time.perf_counter()
    redacted = redact(body.text)
    n_redacted = len(re.findall(r"\[(EMAIL|PHONE|SSN|ID|URL|HANDLE)\]", redacted))
    trace.append(Stage(stage="privacy", status="done", ms=_ms(t),
                       detail=f"{n_redacted} item(s) redacted" if n_redacted
                       else "nothing identifying found"))

    t = time.perf_counter()
    risk = score_risk(redacted)
    escalate = risk >= settings.CRISIS_THRESHOLD
    trace.append(Stage(stage="crisis", status="escalated" if escalate else "done", ms=_ms(t),
                       detail=f"risk {risk:.2f} vs threshold {settings.CRISIS_THRESHOLD:.2f}"))

    if escalate:
        for s in STAGES[2:]:
            trace.append(Stage(stage=s, status="skipped",
                               detail="not run — the crisis rail stops the turn here"))
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
            trace=trace,
        )

    t = time.perf_counter()
    dist = classify(redacted)
    primary = max(dist, key=dist.get) if dist else "unknown"
    model = which()
    trace.append(Stage(stage="mood", status="done", ms=_ms(t),
                       detail=f"{primary} {dist.get(primary, 0):.0%} · model: {model}"))
    for s in ("memory", "conversation", "fidelity"):
        trace.append(Stage(stage=s, status="pending", detail=NOT_BUILT[s]))
    trace.append(Stage(stage="send", status="pending",
                       detail="no reply is sent until Conversation and Fidelity exist"))

    return AnalyzeOut(
        redacted_text=redacted,
        distress=dist,
        primary_emotion=primary,
        crisis_risk=risk,
        escalate=False,
        distress_model=model,
        trace=trace,
    )
