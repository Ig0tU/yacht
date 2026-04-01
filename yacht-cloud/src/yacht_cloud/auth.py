from __future__ import annotations

from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from .db import get_user_by_id, get_user_by_token
from .tokens import parse_access_token

bearer = HTTPBearer(auto_error=False)


def require_user(
    creds: HTTPAuthorizationCredentials | None = Depends(bearer),
) -> dict:
    if not creds:
        raise HTTPException(status_code=401, detail="missing bearer token")
    claims = parse_access_token(creds.credentials)
    user = get_user_by_id(str(claims["sub"])) if claims else None
    if not user:
        # Backward-compatible fallback to opaque token.
        user = get_user_by_token(creds.credentials)
    if not user:
        raise HTTPException(status_code=401, detail="invalid token")
    return user
