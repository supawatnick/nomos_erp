import hashlib
import json
from collections.abc import Mapping
from typing import Any

SENSITIVE_KEYS = {"password", "password_hash", "token", "authorization", "secret", "credential"}


def request_fingerprint(payload: Mapping[str, Any]) -> str:
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(canonical.encode()).hexdigest()


def redact_audit_metadata(metadata: Mapping[str, Any]) -> dict[str, Any]:
    return {
        key: "[REDACTED]" if key.lower() in SENSITIVE_KEYS else value
        for key, value in metadata.items()
    }
