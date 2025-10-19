import base64
import hmac
import hashlib
import json
import os
import time
from typing import Any, Dict

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from .database import SessionLocal
from . import crud, schemas

AUTH_SECRET = os.getenv("AUTH_SECRET", "super-secret-key")
AUTH_TOKEN_TTL = int(os.getenv("AUTH_TOKEN_TTL", "604800"))  # default 7 days

_bearer_scheme = HTTPBearer(auto_error=False)


def _urlsafe_b64encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode("utf-8").rstrip("=")


def _urlsafe_b64decode(data: str) -> bytes:
    padding = "=" * (-len(data) % 4)
    return base64.urlsafe_b64decode(data + padding)


def _sign(segment: str) -> str:
    signature = hmac.new(
        AUTH_SECRET.encode("utf-8"),
        segment.encode("utf-8"),
        hashlib.sha256,
    ).digest()
    return _urlsafe_b64encode(signature)


def create_access_token(user_id: int, expires_in: int = AUTH_TOKEN_TTL) -> str:
    payload: Dict[str, Any] = {
        "sub": user_id,
        "exp": int(time.time()) + expires_in,
    }
    body = _urlsafe_b64encode(json.dumps(payload, separators=(",", ":")).encode("utf-8"))
    signature = _sign(body)
    return f"{body}.{signature}"


def _decode_access_token(token: str) -> Dict[str, Any]:
    try:
        body, signature = token.split(".")
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token",
        ) from exc

    expected_signature = _sign(body)
    if not hmac.compare_digest(signature, expected_signature):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token",
        )

    try:
        payload = json.loads(_urlsafe_b64decode(body))
    except (json.JSONDecodeError, ValueError) as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token",
        ) from exc

    exp = payload.get("exp")
    if not isinstance(exp, int) or exp < int(time.time()):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication token expired",
        )

    return payload


def _get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(_bearer_scheme),
    db: Session = Depends(_get_db),
) -> schemas.User:
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )

    payload = _decode_access_token(credentials.credentials)
    user_id = payload.get("sub")
    if not isinstance(user_id, int):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token",
        )

    user = crud.get_user(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )

    # Attach transient admin flag to the ORM instance for downstream serializers.
    setattr(user, "is_admin", user.username == os.getenv("ADMIN_USER", crud.DEFAULT_USER_USERNAME))
    return user
