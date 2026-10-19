"""Small-group shared contracts. These never include a private profile."""

from typing import Literal

from pydantic import Field, model_validator

from .work_planning import JointPlanningContext, SharedParticipant, SharedPlanningPreferences
from .work_profile import CommunicationToken, InterestToken, ValueToken


class GroupPreferences(SharedPlanningPreferences):
    origin_area: str = Field(min_length=2, max_length=60)
    max_travel_minutes: int = Field(ge=0, le=240)
    avoid_interests: list[InterestToken] = Field(max_length=10)
    values: list[ValueToken] = Field(max_length=5)
    communication_preferences: list[CommunicationToken] = Field(max_length=5)
    allow_shared_ai: bool
    allow_romance_analysis: bool

    @model_validator(mode="after")
    def shared_only(self):
        import re

        from .work_profile import PRIVATE_LABEL_TERMS, PUBLIC_LABEL_PATTERN

        if not re.fullmatch(PUBLIC_LABEL_PATTERN, self.origin_area) or re.search(
            PRIVATE_LABEL_TERMS, self.origin_area, re.I
        ):
            raise ValueError("coarse_area_required")
        if set(self.interests) & set(self.avoid_interests):
            raise ValueError("contradictory_interests")
        if any(
            len(v) != len(set(v))
            for v in (self.avoid_interests, self.values, self.communication_preferences)
        ):
            raise ValueError("duplicate_preferences")
        return self


class GroupParticipant(SharedParticipant):
    preferences: GroupPreferences


class GroupContext(JointPlanningContext):
    schema_version: Literal["group-1.0"]
    participants: list[GroupParticipant] = Field(min_length=2, max_length=8)

    @model_validator(mode="after")
    def separate(self):
        ids = [p.public_id for p in self.participants]
        if len(set(ids)) != len(ids) or ids != sorted(ids):
            raise ValueError("group_context_mismatch")
        if any(p.preferences.mode != self.mode for p in self.participants):
            raise ValueError("group_mode_mismatch")
        if self.mode == "dating" and len(ids) != 2:
            raise ValueError("romance_requires_two_participants")
        return self
