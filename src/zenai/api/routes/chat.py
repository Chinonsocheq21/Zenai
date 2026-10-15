"""A full turn: message in, a reply the Fidelity Monitor has checked, out."""

from __future__ import annotations

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


@router.post("/chat")
def chat(body: ChatIn) -> dict:
    from zenai import llm
    from zenai.agents import turn

    if not llm.available():
        raise HTTPException(503, "No language model configured (XAI_API_KEY in .env).")
    try:
        return turn.run(body.text, [m.model_dump() for m in body.history], body.monitor)
    except llm.LLMError as e:
        raise HTTPException(502, str(e)) from e
