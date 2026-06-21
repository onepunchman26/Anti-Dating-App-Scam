import hashlib
import json
from copy import deepcopy
from typing import Any


def without_signature(document: dict[str, Any]) -> dict[str, Any]:
    unsigned = deepcopy(document)
    unsigned.pop("signature", None)
    return unsigned


def canonical_json(document: dict[str, Any]) -> str:
    return json.dumps(document, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def document_hash(document: dict[str, Any], *, exclude_signature: bool = True) -> str:
    payload = without_signature(document) if exclude_signature else document
    return sha256_text(canonical_json(payload))
