from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles

from zenai.api.routes import analyze, health


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
    yield


app = FastAPI(
    lifespan=lifespan,
    title="ZenAI",
    description="An AI counselor that stays inside the protocol. COSC 490 Project 5, Group 3.",
    version="0.1.0",
)
app.include_router(health.router)
app.include_router(analyze.router)

# The console is served by the API itself: one process, no CORS, nothing to
# configure on demo day. Open http://127.0.0.1:8000/ .
WEB = Path(__file__).resolve().parent.parent / "web"
app.mount("/app", StaticFiles(directory=WEB, html=True), name="web")


@app.get("/", include_in_schema=False)
def root() -> RedirectResponse:
    return RedirectResponse("/app/")
