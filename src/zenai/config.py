from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    DATABASE_URL: str = "postgresql+psycopg://zenai:zenai@localhost:5432/zenai"
    REDIS_URL: str = "redis://localhost:6379/0"

    # Deliberately below 0.5: we favour recall on the crisis classifier.
    # A missed crisis and a false alarm are not the same kind of error.
    CRISIS_THRESHOLD: float = 0.35

    CRISIS_HOTLINE: str = "988"
    CAMPUS_COUNSELING_NAME: str = "Morgan State University Counseling Center"
    CAMPUS_COUNSELING_PHONE: str = ""


settings = Settings()
