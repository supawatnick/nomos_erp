from dataclasses import dataclass
from hashlib import pbkdf2_hmac, sha256
from hmac import compare_digest
from secrets import token_urlsafe
from uuid import UUID

from fastapi import HTTPException, status


@dataclass(frozen=True)
class RequestContext:
    request_id: UUID
    actor_user_id: UUID
    tenant_id: UUID
    tenant_user_id: UUID
    permissions: frozenset[str]
    channel: str = "WEB"


def require_permission(context: RequestContext, permission: str) -> None:
    if permission not in context.permissions:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail={"code": "PERMISSION_DENIED"}
        )


def hash_session_token(token: str) -> str:
    return sha256(token.encode()).hexdigest()


def new_session_token() -> str:
    return token_urlsafe(32)


def hash_password(password: str, salt: bytes) -> str:
    digest = pbkdf2_hmac("sha256", password.encode(), salt, 600_000)
    return "pbkdf2_sha256$600000$" + salt.hex() + "$" + digest.hex()


def verify_password(password: str, encoded: str) -> bool:
    try:
        algorithm, rounds, salt_hex, expected = encoded.split("$", 3)
        if algorithm != "pbkdf2_sha256":
            return False
        actual = pbkdf2_hmac(
            "sha256", password.encode(), bytes.fromhex(salt_hex), int(rounds)
        ).hex()
        return compare_digest(actual, expected)
    except (ValueError, TypeError):
        return False
