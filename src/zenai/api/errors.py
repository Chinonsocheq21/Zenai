"""Error monitoring that can't leak what a student wrote.

Every unexpected error becomes one structured log line, which Vercel keeps and
`vercel logs` shows: the route, the method, the error's type and where in our
code it was raised. Never the error's message, never the request body, never
headers: any of those could carry a student's words. The student gets a calm
reply that points to 988, never a stack trace.

It is a pure ASGI middleware, not an exception handler, because Starlette's
ServerErrorMiddleware re-raises after running an `Exception` handler, and the
server (uvicorn, Vercel's runtime) then logs the full traceback and message
(Engineering review H4). This middleware sits inside that one, catches
everything, and never re-raises, so nothing is left for it to log.
"""

from __future__ import annotations

import json
import logging
import traceback
from pathlib import Path

from fastapi import FastAPI
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


def report(scope: dict, exc: BaseException) -> dict:
    route = scope.get("route")
    entry = {
        "event": "error",
        "route": getattr(route, "path", None) or "unmatched",   # the template, e.g. /chat, never the query
        "method": scope.get("method", ""),
        "type": type(exc).__name__,
        "where": where(exc),
    }
    log.error(json.dumps(entry))
    return entry


class CatchAll:
    """Every unexpected error: one text-free line, the calm 500, no re-raise."""

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        started = False

        async def tracked(message):
            nonlocal started
            if message["type"] == "http.response.start":
                started = True
            await send(message)

        try:
            await self.app(scope, receive, tracked)
        except Exception as exc:  # noqa: BLE001 -- the whole point: nothing escapes
            try:
                report(scope, exc)
            except Exception:  # noqa: BLE001, S110 -- reporting must never be the thing that leaks
                pass
            if not started:
                await JSONResponse(status_code=500, content={"detail": {"message": CALM}})(scope, receive, send)
        # The exception (and its traceback, which holds the request's locals) is dropped here.


class _NoTracebacks(logging.Filter):
    """Belt and braces for the server's own loggers: keep the line, drop the
    traceback and the exception's message."""

    def filter(self, record: logging.LogRecord) -> bool:
        if record.exc_info:
            exc = record.exc_info[1]
            record.exc_info, record.exc_text = None, None
            record.msg, record.args = f"unhandled {type(exc).__name__} (details withheld)", ()
        return True


def install(app: FastAPI) -> None:
    app.add_middleware(CatchAll)
    for name in ("uvicorn.error", "uvicorn.asgi"):
        lg = logging.getLogger(name)
        if not any(isinstance(f, _NoTracebacks) for f in lg.filters):
            lg.addFilter(_NoTracebacks())
