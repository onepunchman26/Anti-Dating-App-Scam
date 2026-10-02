"""UI-independent validation for the opt-in, self-declared adult experiment.

An age declaration is an eligibility gate, never proof of identity or age.
"""

from __future__ import annotations

import unicodedata

MIN_AGE = 18
MAX_AGE = 120


def clean_text(value: str, label: str, max_length: int) -> str:
    if not isinstance(value, str):
        raise ValueError(f"{label} must be text.")
    value = value.strip()
    if len(value) > max_length:
        raise ValueError(f"{label} must be at most {max_length} characters.")
    if any(unicodedata.category(char).startswith("C") or char in "<>" for char in value):
        raise ValueError(f"{label} must not contain control characters or '<'/'>'.")
    return value


def validate_ages(age: int | None, minimum: int | None, maximum: int | None) -> None:
    if age is None:
        raise ValueError("An adult age declaration is required; this service is adults-only.")
    for label, value in (("age", age), ("seeking_age_min", minimum),
                         ("seeking_age_max", maximum)):
        if value is not None and (type(value) is not int or not MIN_AGE <= value <= MAX_AGE):
            raise ValueError(
                f"{label} must be a whole number between {MIN_AGE} and {MAX_AGE}; "
                "this service is adults-only."
            )
    if minimum is not None and maximum is not None and minimum > maximum:
        raise ValueError("seeking_age_min must not exceed seeking_age_max.")


def validate_fingerprint(value: str) -> str:
    if not isinstance(value, str) or len(value) != 64:
        raise ValueError("fingerprint must be a 64-character SHA-256 hex digest.")
    value = value.lower()
    if any(char not in "0123456789abcdef" for char in value):
        raise ValueError("fingerprint must be a 64-character SHA-256 hex digest.")
    return value
