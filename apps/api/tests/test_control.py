from app.domain.control import redact_audit_metadata, request_fingerprint


def test_request_fingerprint_is_deterministic() -> None:
    assert request_fingerprint({"b": 2, "a": 1}) == request_fingerprint({"a": 1, "b": 2})
    assert request_fingerprint({"a": 1}) != request_fingerprint({"a": 2})


def test_audit_metadata_redacts_secrets() -> None:
    result = redact_audit_metadata(
        {"action": "role.updated", "token": "secret", "password": "never-log"}
    )
    assert result["action"] == "role.updated"
    assert result["token"] == "[REDACTED]"
    assert result["password"] == "[REDACTED]"
