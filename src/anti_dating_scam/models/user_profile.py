from pydantic import BaseModel, Field


class UserProfilePreferences(BaseModel):
    """Minimal placeholder for future local-first settings, not personality scoring."""

    safety_reminders_enabled: bool = True
    data_retention_days: int = Field(default=30, ge=0)
    allow_cross_platform_imports: bool = False
