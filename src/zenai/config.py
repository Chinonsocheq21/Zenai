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
    # which model writes drafts, and which gives the Fidelity Monitor its second opinion
    DRAFT_MODEL: str = "grok-4.20-0309-non-reasoning"  # 2.4 s vs 8.4 s median, no more drift (results/speed_eval.json)
    JUDGE_MODEL: str = "grok-4.3"
    LLM_BASE_URL: str = "https://api.x.ai/v1"
    # How many times a drifting draft may be rewritten before the safe fallback.
    MAX_REWRITES: int = 2
    # Ask the model for a second opinion on whatever the drift detector flags.
    SECOND_OPINION: bool = True
    # specialist routing: a fast non-reasoning model, rules if it is off or down
    ROUTER_LLM: bool = True
    ROUTER_MODEL: str = "grok-4.20-0309-non-reasoning"
    # live pipeline events for /workflow/ (testing phase; redacted text only, memory only)
    WORKFLOW_EVENTS: bool = True
    # a fast model also screens for indirect crisis language (can only raise risk)
    CRISIS_SCREEN: bool = True
    # ZenAI's spoken voice in voice mode: a neural voice, calm and a little slow
    TTS_VOICE: str = "en-US-AvaMultilingualNeural"
    TTS_RATE: str = "-8%"
    # usage limits, so a shared link cannot drain the xAI credits. A crisis message is
    # always answered with the hand-off, limited or not.
    LIMIT_PER_10MIN: int = 20          # messages per device in any 10 minutes
    LIMIT_PER_DAY: int = 150           # messages per device per day
    LIMIT_GLOBAL_DAY: int = 3000       # model-backed messages per day, everyone together
    LIMIT_TTS_PER_10MIN: int = 80      # spoken-reply clips per device in any 10 minutes
    # class demo: when set, the student app asks for this code before it will talk
    ACCESS_CODE: str = ""
    PUBLIC_URL: str = ""               # the hosted address, once there is one; used by the QR page

    CRISIS_HOTLINE: str = "988"
    CAMPUS_COUNSELING_NAME: str = "Morgan State University Counseling Center"
    # Verified 2026-10-15 on morgan.edu/counseling-center/about-us/contact-us.
    # The office line alone is not enough: the scenario this exists for is 2 a.m.,
    # when the office is closed, so the 24/7 line is part of the value.
    CAMPUS_COUNSELING_PHONE: str = "443-885-3130 (weekdays 8:30–5) · 24/7: 1-800-422-0009"


settings = Settings()
