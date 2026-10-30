"""A full turn: message in, a reply the Fidelity Monitor has checked, out."""

from __future__ import annotations

from typing import Literal

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from zenai.api import limits

router = APIRouter(tags=["chat"])


class Msg(BaseModel):
    role: str
    content: str


class ChatIn(BaseModel):
    text: str = Field(..., min_length=1, max_length=4000)
    history: list[Msg] = []
    monitor: bool = True  # False only for experiment E1's baseline
    # Notes the student explicitly chose to let ZenAI remember. Kept on the
    # student's own device and sent with each message; never stored here.
    memory: list[str] = Field(default_factory=list, max_length=10)
    # which screen sent it, so the workflow viewer can label the turn
    client: str = Field("api", max_length=20)
    # today's check-in from the app, if the student did one (it never leaves
    # the phone otherwise). Read by the crisis check and the Conversation Agent.
    checkin: Literal["Light", "A bit much", "Heavy", "Very heavy", "I'm not okay"] | None = None


def _limited_turn(body: ChatIn) -> dict:
    """Over the limit: no model is called, but the crisis check still runs on the
    patterns and the conversation rules, so a student in crisis is never told to
    come back later."""
    from zenai.agents.privacy import redact
    from zenai.config import settings
    from zenai.models.crisis import assess

    redacted = redact(body.text)
    earlier = [m.content for m in body.history if m.role == "user"]
    a = assess(redacted, earlier, body.checkin, screen=False)
    if a["risk"] >= settings.CRISIS_THRESHOLD:
        return {"escalate": True, "crisis_risk": a["risk"], "redacted_text": redacted, "reply": None, "attempts": [],
                "trace": [], "escalation": {"hotline": settings.CRISIS_HOTLINE, "campus": settings.CAMPUS_COUNSELING_NAME,
                                            "phone": settings.CAMPUS_COUNSELING_PHONE, "action": "human_handoff"},
                "note": "Usage limit reached; the crisis check still ran."}
    raise HTTPException(429, {"limited": True, "message": limits.PAUSE})


def _local_tool(req: Request) -> bool:
    # the console and the workflow viewer on this laptop are not rate limited
    return (req.client.host if req.client else "") in limits.LOCAL and not req.headers.get("x-zenai-device")


@router.post("/chat")
def chat(body: ChatIn, req: Request) -> dict:
    from zenai import llm
    from zenai.agents import turn

    limits.check_code(req)
    if not _local_tool(req) and not limits.allow(req, "chat"):
        return _limited_turn(body)
    if not llm.available():
        raise HTTPException(503, "No language model configured (XAI_API_KEY in .env).")
    try:
        return turn.run(body.text, [m.model_dump() for m in body.history], body.monitor,
                        memory=[m[:200] for m in body.memory], client=body.client, checkin=body.checkin)
    except llm.LLMError as e:
        raise HTTPException(502, str(e)) from e


class CloseIn(BaseModel):
    history: list[Msg] = []
    client: str = Field("api", max_length=20)


@router.post("/chat/close")
def close(body: CloseIn, req: Request) -> dict:
    """'I'm done for now': a short goodbye that hands back what the student said
    matters to them, checked by the Fidelity Monitor like any reply."""
    from zenai import llm
    from zenai.agents import conversation

    limits.check_code(req)
    if not llm.available() or (not _local_tool(req) and not limits.allow(req, "chat")):
        return {"reply": conversation.CLOSE_FALLBACK, "fallback": True}
    return conversation.close([m.model_dump() for m in body.history])


@router.get("/resources")
def resources() -> dict:
    """Crisis resources, one source for every page that shows them."""
    from zenai.config import settings

    return {"hotline": settings.CRISIS_HOTLINE, "campus": settings.CAMPUS_COUNSELING_NAME,
            "phone": settings.CAMPUS_COUNSELING_PHONE or "NOT CONFIGURED"}
