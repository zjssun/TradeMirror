from __future__ import annotations

import secrets

from fastapi import Header, HTTPException, status

from app.config import Settings


def require_launch_token(
    settings: Settings,
    x_trademirror_token: str | None = Header(default=None),
) -> None:
    if not x_trademirror_token or not secrets.compare_digest(
        x_trademirror_token, settings.launch_token
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid engine access token",
        )
