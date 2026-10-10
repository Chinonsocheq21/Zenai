from fastapi import APIRouter

router = APIRouter(tags=["health"])


@router.get("/health")
def health() -> dict:
    """M0 acceptance test. All three read "ok" or M0 is not done."""
    out = {"db": "down", "redis": "down", "models": "down"}
    try:
        from sqlalchemy import text

        from zenai.db.session import engine

        with engine.connect() as c:
            c.execute(text("SELECT 1"))
        out["db"] = "ok"
    except Exception as e:  # noqa: BLE001
        out["db"] = f"error: {e.__class__.__name__}"
    try:
        import redis

        from zenai.config import settings

        redis.Redis.from_url(settings.REDIS_URL).ping()
        out["redis"] = "ok"
    except Exception as e:  # noqa: BLE001
        out["redis"] = f"error: {e.__class__.__name__}"
    try:
        from pathlib import Path

        out["models"] = "ok" if Path("models/distress").exists() else "not trained yet"
    except Exception as e:  # noqa: BLE001
        out["models"] = f"error: {e.__class__.__name__}"
    return out
