"""GET /campus: the student-facing campus details, so the app shows the right numbers.

Public and unauthenticated: these are the same numbers printed on the campus
website. Comes from the registry file, so it answers with the database, Redis
and the language model all down.
"""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, HTTPException

from zenai import campuses

router = APIRouter(tags=["campus"])


@router.get("/campus")
def campus(id: Optional[str] = None) -> dict:  # noqa: UP045 (FastAPI reads it at runtime on 3.9)
    """Names, numbers, hours, 24/7 line and timezone for one campus (default Morgan)."""
    c = campuses.get(id) if id else campuses.default()
    if c is None:
        raise HTTPException(404, {"message": f"No campus {id!r}."})
    return campuses.public(c)
