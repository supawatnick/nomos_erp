from os import urandom
from uuid import uuid4

import pytest
from fastapi import HTTPException

from app.domain.security import (
    RequestContext,
    hash_password,
    hash_session_token,
    require_permission,
    verify_password,
)


def context(*permissions: str) -> RequestContext:
    return RequestContext(uuid4(), uuid4(), uuid4(), uuid4(), frozenset(permissions))


def test_rbac_deny_by_default() -> None:
    with pytest.raises(HTTPException) as exc:
        require_permission(context(), "organization.manage")
    assert exc.value.status_code == 403


def test_rbac_allows_explicit_permission() -> None:
    require_permission(context("organization.manage"), "organization.manage")


def test_session_tokens_are_hashed() -> None:
    token = "secret-session-token"
    assert hash_session_token(token) != token
    assert len(hash_session_token(token)) == 64


def test_password_hash_roundtrip_and_wrong_password() -> None:
    encoded = hash_password("correct horse battery staple", urandom(16))
    assert "correct horse" not in encoded
    assert verify_password("correct horse battery staple", encoded)
    assert not verify_password("wrong", encoded)


@pytest.mark.parametrize(
    ("granted", "required", "allowed"),
    [
        ({"organization.read"}, "organization.read", True),
        ({"organization.read"}, "organization.manage", False),
        ({"user.manage"}, "role.manage", False),
        ({"role.manage"}, "role.manage", True),
        ({"audit.read"}, "audit.read", True),
        (set(), "tenant.read", False),
    ],
)
def test_rbac_permission_matrix(granted: set[str], required: str, allowed: bool) -> None:
    if allowed:
        require_permission(context(*granted), required)
    else:
        with pytest.raises(HTTPException):
            require_permission(context(*granted), required)
