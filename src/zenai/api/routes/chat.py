"""A full turn: message in, a reply the Fidelity Monitor has checked, out."""

from __future__ import annotations

from typing import Literal

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

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


@router.post("/chat")
def chat(body: ChatIn) -> dict:
    from zenai import llm
    from zenai.agents import turn

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
def close(body: CloseIn) -> dict:
    """'I'm done for now': a short goodbye that hands back what the student said
    matters to them, checked by the Fidelity Monitor like any reply."""
    from zenai import llm
    from zenai.agents import conversation

    if not llm.available():
        return {"reply": conversation.CLOSE_FALLBACK, "fallback": True}
    return conversation.close([m.model_dump() for m in body.history])


@router.get("/resources")
def resources() -> dict:
    """Crisis resources, one source for every page that shows them."""
    from zenai.config import settings

    return {"hotline": settings.CRISIS_HOTLINE, "campus": settings.CAMPUS_COUNSELING_NAME,
            "phone": settings.CAMPUS_COUNSELING_PHONE or "NOT CONFIGURED"}
