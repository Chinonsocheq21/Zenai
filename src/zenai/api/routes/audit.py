"""The blind marking page for Experiment E1, at /audit/.

Serves the shuffled replies from results/e1/<tag>/audit_replies.csv WITHOUT
the condition (monitor on or off), and saves each mark as it is made to
results/e1/<tag>/marks-<rater>.json. On this machine it just works. From
anywhere else (a teammate on the tunnel link) it needs the class code and a
rater name, so each teammate's marks land in their own file and nobody can
overwrite the owner's "human" sheet.
"""

from __future__ import annotations

import csv
import json
import re
from pathlib import Path

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from zenai.api import limits

router = APIRouter(tags=["audit"])
ROOT = Path(__file__).resolve().parents[4] / "results" / "e1"
RATER = re.compile(r"^[a-z0-9-]{1,20}$")


def _allowed(req: Request, rater: str) -> None:
    from zenai.config import settings

    if not RATER.match(rater):
        raise HTTPException(422, "Rater names are lowercase letters, digits and dashes.")
    if limits.is_local(req):
        return
    if settings.ACCESS_CODE and rater != "human":
        limits.check_code(req)
        return
    raise HTTPException(403, {"code_required": True, "message": "Enter your name and the team code to mark."})


def _dir(tag: str) -> Path:
    d = ROOT / tag
    if not tag.replace("-", "").replace("_", "").isalnum() or not (d / "audit_replies.csv").exists():
        raise HTTPException(404, f"No audit sheet for {tag}")
    return d


@router.get("/audit/items")
def items(tag: str, req: Request, rater: str = "human") -> dict:
    _allowed(req, rater)
    d = _dir(tag)
    rows = list(csv.DictReader((d / "audit_replies.csv").open()))
    marks_path = d / f"marks-{rater}.json"
    marks = json.loads(marks_path.read_text()) if marks_path.exists() else {}
    return {"tag": tag, "items": [{"id": r["item_id"], "message": r["student_message"], "reply": r["zenai_reply"]}
                                  for r in rows], "marks": marks}


class Mark(BaseModel):
    tag: str
    id: str = Field(..., max_length=10)
    advice: bool = False
    reassurance: bool = False
    diagnosis: bool = False
    note: str = Field("", max_length=300)
    rater: str = Field("human", pattern="^[a-z0-9-]{1,20}$")


@router.post("/audit/mark")
def mark(m: Mark, req: Request) -> dict:
    _allowed(req, m.rater)
    d = _dir(m.tag)
    p = d / f"marks-{m.rater}.json"
    marks = json.loads(p.read_text()) if p.exists() else {}
    marks[m.id] = {"advice": m.advice, "reassurance": m.reassurance, "diagnosis": m.diagnosis, "note": m.note}
    p.write_text(json.dumps(marks, indent=1, sort_keys=True))
    return {"saved": len(marks)}
