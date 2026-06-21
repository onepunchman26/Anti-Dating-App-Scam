import os
from functools import lru_cache

from pydantic import BaseModel


class Settings(BaseModel):
    app_name: str = "AI-SlowMatch"
    environment: str = "development"
    ai_provider: str = "mock"
    log_level: str = "INFO"


@lru_cache
def get_settings() -> Settings:
    return Settings(
        app_name=os.getenv("APP_NAME", "AI-SlowMatch"),
        environment=os.getenv("ENVIRONMENT", "development"),
        ai_provider=os.getenv("AI_PROVIDER", "mock"),
        log_level=os.getenv("LOG_LEVEL", "INFO"),
    )
