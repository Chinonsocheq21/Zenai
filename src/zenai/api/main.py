import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles

from zenai.api import errors
from zenai.api.routes import (
    aggregate,
    analyze,
    audit,
    auth,
    campus,
    chat,
    checkins,
    classroom,
    fidelity,
    health,
    pilot,
    tts,
    workflow,
)


@asynccontextmanager
async def lifespan(_: FastAPI):
    # Load the distress model at boot, not on the first message. Cold, the first
    # /analyze took 6.5 s while sklearn and the pipeline loaded -- a dead pause on
    # the first message of a live demo. Warm, a turn is a few milliseconds.
    try:
        from zenai.models.distress import classify

        classify("warm up")
    except RuntimeError as e:  # no trained model yet: the API still starts
        print(f"[zenai] distress model not loaded: {e}")
    try:
        from zenai.models import fidelity

        if fidelity.available():
            fidelity.check("warm up.")
    except RuntimeError as e:
        print(f"[zenai] drift detector not loaded: {e}")
    # Warm the speech service in the background: the first request pays ~3.5 s of
    # connection setup, every later one starts speaking in ~0.3 s.
    import asyncio

    async def _warm_voice():
        try:
            import edge_tts

            from zenai.config import settings

            async for _ in edge_tts.Communicate("Hi.", settings.TTS_VOICE).stream():
                pass
        except Exception:  # noqa: BLE001, S110 -- voice is optional; the app falls back
            pass

    task = asyncio.create_task(_warm_voice())
    yield
    task.cancel()


# No /docs, /redoc or /openapi.json: api/index.py mounts this app, so turning
# them off on the outer app alone left /api/docs open (Engineering review M4).
app = FastAPI(
    lifespan=lifespan,
    title="ZenAI",
    description="A student support tool whose replies are checked against the protocol before they are sent.",
    version="0.1.0",
    docs_url=None,
    redoc_url=None,
    openapi_url=None,
)

MAX_BODY = 1_000_000    # bytes. A message, 16 turns of history and 10 notes fit many times over.
SECURITY_HEADERS = [
    (b"x-content-type-options", b"nosniff"),
    (b"x-frame-options", b"DENY"),
    (b"content-security-policy", b"frame-ancestors 'none'"),
    (b"referrer-policy", b"no-referrer"),
]


class Guard:
    """Pure ASGI, so nothing here touches the body or logs anything.
      * marks whether the request was made on this machine, which is the only
        place the research switches (monitor off, the turn log) work;
      * refuses bodies over MAX_BODY before they are read;
      * adds framing and sniffing headers to every response."""

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        from starlette.requests import Request

        from zenai.agents import turn
        from zenai.api import limits

        size = dict(scope.get("headers") or []).get(b"content-length", b"0")
        if size.isdigit() and int(size) > MAX_BODY:
            await JSONResponse(status_code=413, content={"detail": {"message": "That message is too long to send."}})(
                scope, receive, send)
            return

        async def headed(message):
            if message["type"] == "http.response.start":
                have = {k.lower() for k, _ in message.get("headers", [])}
                message["headers"] = list(message.get("headers", [])) + [
                    (k, v) for k, v in SECURITY_HEADERS if k not in have]
                if os.environ.get("VERCEL") and b"strict-transport-security" not in have:
                    message["headers"].append((b"strict-transport-security", b"max-age=63072000; includeSubDomains"))
            await send(message)

        token = turn.REQUEST_LOCAL.set(limits.is_local(Request(scope)))
        try:
            await self.app(scope, receive, headed)
        finally:
            turn.REQUEST_LOCAL.reset(token)


app.add_middleware(Guard)
errors.install(app)     # last, so it wraps everything above
app.include_router(health.router)
app.include_router(analyze.router)
app.include_router(fidelity.router)
app.include_router(chat.router)
app.include_router(workflow.router)
app.include_router(audit.router)
app.include_router(tts.router)
app.include_router(classroom.router)
app.include_router(auth.router)
app.include_router(checkins.router)
app.include_router(pilot.router)
app.include_router(aggregate.router)
app.include_router(campus.router)

# The console is served by the API itself: one process, no CORS, nothing to
# configure on demo day. Open http://127.0.0.1:8000/ .
WEB = Path(__file__).resolve().parent.parent / "web"
app.mount("/app", StaticFiles(directory=WEB, html=True), name="web")
STUDENT = Path(__file__).resolve().parent.parent / "student"
app.mount("/student", StaticFiles(directory=STUDENT, html=True), name="student")
WORKFLOW = Path(__file__).resolve().parent.parent / "workflow"
app.mount("/workflow", StaticFiles(directory=WORKFLOW, html=True), name="workflow")
PRESENT = Path(__file__).resolve().parent.parent / "present"
app.mount("/present", StaticFiles(directory=PRESENT, html=True), name="present")
AUDIT = Path(__file__).resolve().parent.parent / "audit"
app.mount("/audit", StaticFiles(directory=AUDIT, html=True), name="audit")


@app.get("/", include_in_schema=False)
def root() -> RedirectResponse:
    return RedirectResponse("/app/")
