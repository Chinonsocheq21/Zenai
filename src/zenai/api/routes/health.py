from fastapi import APIRouter

router = APIRouter(tags=["health"])


@router.get("/health")
def health() -> dict:
    """What the service can reach. Chat never depends on db or limits: a crisis
    is handed off with all of them down."""
    import os
    from pathlib import Path

    from zenai.db import store

    models = Path(__file__).resolve().parents[4] / "models"
    limits_store = "redis" if (os.environ.get("KV_REST_API_URL") or os.environ.get("UPSTASH_REDIS_REST_URL")) else "memory"
    return {
        "db": "ok" if store.ping() else "unavailable",
        "limits": limits_store,
        "models": "ok" if (models / "distress").exists() and (models / "fidelity").exists() else "missing",
    }
