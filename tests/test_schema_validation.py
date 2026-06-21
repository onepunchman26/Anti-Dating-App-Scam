import pytest

from anti_dating_scam.engine.personal_profile_builder import PersonalProfileBuilder
from anti_dating_scam.reports.schema_validator import SchemaValidationError, validate_document


def test_profile_schema_validation_rejects_missing_required_fields() -> None:
    with pytest.raises(SchemaValidationError):
        validate_document({"schema_version": "0.1"}, "personal_profile.schema.json")


def test_profile_schema_validation_accepts_generated_profile() -> None:
    profile = PersonalProfileBuilder().build(manual_notes="I value honesty and slow trust.")

    validate_document(profile, "personal_profile.schema.json")
