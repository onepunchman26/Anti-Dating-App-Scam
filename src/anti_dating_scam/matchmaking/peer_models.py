"""Approved adult matching contracts; never a private personality database."""

from __future__ import annotations

import re
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

DIMENSIONS = {
    "intention": ("long_term", "casual", "unsure"),
    "pace": ("slow", "steady", "flexible"),
    "communication": ("direct", "reflective", "mixed"),
    "availability": ("weekdays", "weekends", "flexible"),
    "smoking": ("no", "sometimes", "yes"),
    "interests": ("reading", "music", "art", "outdoors", "cooking", "games", "travel", "sport"),
}


class Contract(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    @field_validator("approved", mode="before", check_fields=False)
    @classmethod
    def approval_is_boolean(cls, value):
        if value is not True:
            raise ValueError("Explicit approval is required.")
        return value


class AdultDeclaration(Contract):
    age: int = Field(ge=18, le=120, strict=True)
    adult_confirmed: Literal[True]

    @field_validator("adult_confirmed", mode="before")
    @classmethod
    def explicit(cls, value):
        if value is not True:
            raise ValueError("An explicit adult declaration is required.")
        return value


class Attribute(Contract):
    values: list[str] = Field(min_length=1, max_length=5)
    disclose: bool = False


class MatchingProfile(AdultDeclaration):
    alias: str = Field(min_length=1, max_length=40, pattern=r"\S")
    city: str = Field(min_length=2, max_length=60)
    areas: list[str] = Field(min_length=1, max_length=5)
    show_city: bool = False
    age_min: int = Field(default=18, ge=18, le=120, strict=True)
    age_max: int = Field(default=120, ge=18, le=120, strict=True)
    attributes: dict[str, Attribute] = Field(default_factory=dict, max_length=6)
    required: dict[str, list[str]] = Field(default_factory=dict, max_length=6)
    priorities: list[str] = Field(default_factory=lambda: ["intention", "availability"])
    process_matching: bool = False
    discoverable: bool = False
    automatic_minutes: int = Field(default=0, ge=0, le=10080, strict=True)
    notifications: bool = False

    @model_validator(mode="after")
    def bounded(self):
        if self.age_min > self.age_max:
            raise ValueError("Invalid adult age range.")
        if self.automatic_minutes and self.automatic_minutes < 15:
            raise ValueError("Automatic discovery is at most every 15 minutes.")
        if (self.discoverable or self.automatic_minutes) and not self.process_matching:
            raise ValueError("Matching processing requires explicit permission.")
        if len(self.priorities) > 6 or len(set(self.priorities)) != len(self.priorities):
            raise ValueError("Choose distinct priorities.")
        for key in self.priorities:
            if key not in DIMENSIONS:
                raise ValueError("Unsupported priority.")
        for key, attribute in self.attributes.items():
            if key not in DIMENSIONS or not set(attribute.values) <= set(DIMENSIONS[key]):
                raise ValueError("Only supported, explicitly confirmed attributes are accepted.")
        for key, values in self.required.items():
            if key not in DIMENSIONS or not values or not set(values) <= set(DIMENSIONS[key]):
                raise ValueError("Invalid hard requirement.")
        for area in [self.city, *self.areas]:
            if not 2 <= len(area) <= 60 or not re.fullmatch(r"[^\d\r\n<>/@:]+", area):
                raise ValueError("Use a city/region name, never an address or coordinates.")
        if re.search(r"[\r\n<>/@]", self.alias):
            raise ValueError("Use a short pseudonym.")
        return self


class ProfileUpdate(Contract):
    expected_version: int = Field(ge=0)
    profile: MatchingProfile
    approved: Literal[True]


class Registration(AdultDeclaration):
    alias: str = Field(min_length=1, max_length=40, pattern=r"^[^\r\n<>/@]+$")


class InviteCreate(Contract):
    request_id: str = Field(pattern=r"^[a-f0-9]{32}$")
    hours: int = Field(default=48, ge=1, le=168)
    intended_member: str | None = Field(default=None, pattern=r"^[a-f0-9]{32}$")


class InviteAction(Contract):
    invitation: str = Field(pattern=r"^[A-Za-z0-9_-]{43}$")
    action: Literal["claim", "approve", "decline", "revoke"]
    allow_cloud_ai: bool = False
    expected_versions: dict[str, int] = Field(default_factory=dict, max_length=2)


class PublicUpdate(Contract):
    expected_version: int = Field(ge=0)
    text: str = Field(default="", max_length=1500)
    publish: bool = False
    approved: Literal[True]


class PairText(Contract):
    en: str = Field(min_length=1, max_length=1000, pattern=r"\S")
    zh: str = Field(min_length=1, max_length=1000, pattern=r"\S")


class PeerEvidence(Contract):
    source: str = Field(pattern=r"^[AB][0-9]{2}$")
    quote: str = Field(min_length=1, max_length=300, pattern=r"\S")


class PeerPoint(Contract):
    text: PairText
    evidence: list[PeerEvidence] = Field(min_length=2, max_length=4)


class PeerReport(Contract):
    alignment: list[PeerPoint] = Field(max_length=5)
    tensions: list[PeerPoint] = Field(max_length=5)
    uncertain_differences: list[PeerPoint] = Field(max_length=5)
    unknowns: list[PairText] = Field(min_length=1, max_length=6)
    questions: list[PairText] = Field(max_length=3)
    caveat: PairText


class CompareFinish(Contract):
    invitation: str = Field(pattern=r"^[A-Za-z0-9_-]{43}$")
    ticket: str = Field(pattern=r"^[a-f0-9]{64}$")
    report: PeerReport


def strict_schema(model):
    """The existing provider interface accepts strict inline JSON schemas."""
    schema = model.model_json_schema()
    definitions = schema.get("$defs", {})

    def walk(value):
        if isinstance(value, list):
            return [walk(item) for item in value]
        if not isinstance(value, dict):
            return value
        if "$ref" in value:
            return walk(definitions[value["$ref"].rsplit("/", 1)[-1]])
        result = {k: walk(v) for k, v in value.items() if k not in {"$defs", "default"}}
        if result.get("type") == "object":
            result["required"] = list(result.get("properties", {}))
            result["additionalProperties"] = False
        return result

    return walk(schema)
