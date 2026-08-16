# WHY: Create and validate JWT access tokens for API authentication.

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from jose import JWTError, jwt

from app.config import get_settings


def create_access_token(subject: str) -> str:
    settings = get_settings()
    expire = datetime.now(UTC) + timedelta(minutes=settings.access_token_expire_minutes)
    payload = {"sub": subject, "exp": expire}
    return jwt.encode(payload, settings.secret_key, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> str | None:
    settings = get_settings()
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.jwt_algorithm])
        sub = payload.get("sub")
        return str(sub) if sub else None
    except JWTError:
        return None
