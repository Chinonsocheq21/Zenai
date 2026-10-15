from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    DATABASE_URL: str = "postgresql+psycopg://zenai:zenai@localhost:5432/zenai"
    REDIS_URL: str = "redis://localhost:6379/0"

    # Deliberately below 0.5: we favour recall on the crisis classifier.
    # A missed crisis and a false alarm are not the same kind of error.
    CRISIS_THRESHOLD: float = 0.35

    # Language model for the Conversation Agent. The key lives in .env only.
    XAI_API_KEY: str = ""
    LLM_MODEL: str = "grok-4.3"
    LLM_BASE_URL: str = "https://api.x.ai/v1"
    # How many times a drifting draft may be rewritten before the safe fallback.
    MAX_REWRITES: int = 2

    CRISIS_HOTLINE: str = "988"
    CAMPUS_COUNSELING_NAME: str = "Morgan State University Counseling Center"
    # Verified 2026-10-15 on morgan.edu/counseling-center/about-us/contact-us.
    # The office line alone is not enough: the scenario this exists for is 2 a.m.,
    # when the office is closed, so the 24/7 line is part of the value.
    CAMPUS_COUNSELING_PHONE: str = "443-885-3130 (weekdays 8:30–5) · 24/7: 1-800-422-0009"


settings = Settings()
