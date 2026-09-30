from fastapi import FastAPI

from zenai.api.routes import analyze, health

app = FastAPI(
    title="ZenAI",
    description="An AI counselor that stays inside the protocol. COSC 490 Project 5, Group 3.",
    version="0.1.0",
)
app.include_router(health.router)
app.include_router(analyze.router)
