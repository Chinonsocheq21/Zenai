"""Feedback ("Did this help?") and the class-demo projector page.

POST /feedback       one tap from the student app, only when the student turned on
                     sharing in Privacy: helpful yes/no, which specialist answered,
                     and ZenAI's own reply. Never the student's message.
GET  /feedback/summary   counts, for the evaluation (this machine only)
GET  /present/info   the address and class code to put on the projector (this machine only)
GET  /qr.svg?data=   a QR code for that address
"""

from __future__ import annotations

import json
import socket
import time
from pathlib import Path

from fastapi import APIRouter, HTTPException, Query, Request
from fastapi.responses import Response
from pydantic import BaseModel, Field

from zenai.api import limits

router = APIRouter(tags=["classroom"])
FEEDBACK = Path(__file__).resolve().parents[4] / "data" / "feedback.jsonl"


def _local(req: Request) -> None:
    if (req.client.host if req.client else "") not in limits.LOCAL:
        raise HTTPException(403, "Only available on this machine.")


class FeedbackIn(BaseModel):
    helpful: bool
    specialist: str | None = Field(None, max_length=40)
    reply: str = Field("", max_length=800)


@router.post("/feedback")
def feedback(body: FeedbackIn, req: Request) -> dict:
    limits.check_code(req)
    if not limits.allow(req, "tts"):          # shares the light bucket; one tap per reply at most
        raise HTTPException(429, {"limited": True, "message": limits.PAUSE})
    FEEDBACK.parent.mkdir(parents=True, exist_ok=True)
    with FEEDBACK.open("a") as f:
        f.write(json.dumps({"at": time.strftime("%Y-%m-%dT%H:%M:%S"), "helpful": body.helpful,
                            "specialist": body.specialist, "reply": body.reply}) + "\n")
    return {"ok": True}


@router.get("/feedback/summary")
def feedback_summary(req: Request) -> dict:
    _local(req)
    rows = [json.loads(x) for x in FEEDBACK.read_text().splitlines()] if FEEDBACK.exists() else []
    by: dict = {}
    for r in rows:
        k = r.get("specialist") or "Conversation Agent"
        b = by.setdefault(k, {"helpful": 0, "not": 0})
        b["helpful" if r["helpful"] else "not"] += 1
    yes = sum(1 for r in rows if r["helpful"])
    return {"total": len(rows), "helpful": yes, "helpful_pct": round(100 * yes / len(rows), 1) if rows else None,
            "by_specialist": by}


def lan_ip() -> str:
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("10.255.255.255", 1))
            return s.getsockname()[0]
    except OSError:
        return "127.0.0.1"


@router.get("/present/info")
def present_info(req: Request) -> dict:
    _local(req)
    from zenai.config import settings

    port = req.url.port or 8000
    lan = f"http://{lan_ip()}:{port}/student/"
    url = (settings.PUBLIC_URL.rstrip("/") + "/student/") if settings.PUBLIC_URL else lan
    return {"lan_url": lan, "public_url": settings.PUBLIC_URL or None, "url": url,
            # the QR carries the code in the fragment, so scanning skips typing it
            "scan_url": url + (f"#code={settings.ACCESS_CODE}" if settings.ACCESS_CODE else ""),
            "code": settings.ACCESS_CODE or None}


@router.get("/qr.svg")
def qr(req: Request, data: str = Query(..., max_length=300)) -> Response:
    _local(req)
    import io

    import segno

    buf = io.BytesIO()
    segno.make(data, error="m").save(buf, kind="svg", scale=12, border=2, dark="#14233D", light="#FFFFFF")
    return Response(buf.getvalue(), media_type="image/svg+xml")
