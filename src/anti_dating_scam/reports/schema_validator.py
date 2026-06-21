import json
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator


class SchemaValidationError(ValueError):
    pass


SCHEMA_DIR = Path(__file__).resolve().parents[1] / "schemas"


def load_schema(schema_name: str) -> dict[str, Any]:
    path = SCHEMA_DIR / schema_name
    if not path.exists():
        raise FileNotFoundError(f"Unknown schema: {schema_name}")
    return json.loads(path.read_text(encoding="utf-8"))


def validate_document(document: dict[str, Any], schema_name: str) -> None:
    schema = load_schema(schema_name)
    validator = Draft202012Validator(schema)
    errors = sorted(validator.iter_errors(document), key=lambda error: error.path)
    if errors:
        first = errors[0]
        path = ".".join(str(part) for part in first.path) or "<root>"
        raise SchemaValidationError(f"{schema_name} validation failed at {path}: {first.message}")


def is_valid(document: dict[str, Any], schema_name: str) -> bool:
    try:
        validate_document(document, schema_name)
    except SchemaValidationError:
        return False
    return True
