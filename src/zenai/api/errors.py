"""Error monitoring that can't leak what a student wrote.

Every unexpected error becomes one structured log line, which Vercel keeps and
`vercel logs` shows: the route, the method, the error's type and where in our
code it was raised. Never the error's message, never the request body, never
headers: any of those could carry a student's words. The student gets a calm
reply that points to 988, never a stack trace.
"""

from __future__ import annotations

import json
import logging
import traceback
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

log = logging.getLogger("zenai.errors")
CALM = "Something went wrong on our side. Please try again. If you need someone right now, call or text 988."


def where(exc: BaseException) -> str:
    """file:line of the deepest frame inside our own code, or the last frame."""
    frames = traceback.extract_tb(exc.__traceback__)
    ours = [f for f in frames if "/zenai/" in f.filename.replace("\\", "/")] or frames
    if not ours:
        return "unknown"
    f = ours[-1]
    return f"{Path(f.filename).name}:{f.lineno}"


def report(request: Request, exc: BaseException) -> dict:
    route = request.scope.get("route")
    entry = {
        "event": "error",
        "route": getattr(route, "path", None) or "unmatched",   # the template, e.g. /chat, never the query
        "method": request.method,
        "type": type(exc).__name__,
        "where": where(exc),
    }
    log.error(json.dumps(entry))
    return entry


def install(app: FastAPI) -> None:
    @app.exception_handler(Exception)
    async def unexpected(request: Request, exc: Exception) -> JSONResponse:
        report(request, exc)
        return JSONResponse(status_code=500, content={"detail": {"message": CALM}})
