"""
Authentication and security module for AccessGuard AI.
- Single demo admin authentication
- Constant-time password comparison
- JWT token generation & verification (HS256)
- In-memory rate limiting for login (5 requests / minute per client IP)
"""

from __future__ import annotations

import secrets
import time
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt

from backend.app.config import get_settings

security_scheme = HTTPBearer(auto_error=False)

# In-memory rate limiter: client_ip -> list of epoch timestamps
_login_attempts: dict[str, list[float]] = defaultdict(list)
LOGIN_RATE_LIMIT = 5        # max attempts
LOGIN_WINDOW_SECONDS = 60   # per 60 seconds


def check_rate_limit(client_ip: str) -> None:
    """Enforce rate limiting on login endpoint."""
    now = time.time()
    cutoff = now - LOGIN_WINDOW_SECONDS
    # Clean up old timestamps
    attempts = [t for t in _login_attempts[client_ip] if t > cutoff]
    if len(attempts) >= LOGIN_RATE_LIMIT:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Too many login attempts. Please wait {LOGIN_WINDOW_SECONDS} seconds.",
        )
    attempts.append(now)
    _login_attempts[client_ip] = attempts


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a signed JWT access token."""
    settings = get_settings()
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(hours=8))
    to_encode.update({"exp": expire, "iat": datetime.now(timezone.utc)})
    return jwt.encode(to_encode, settings.secret_key, algorithm="HS256")


def verify_password(plain_password: str, expected_password: str) -> bool:
    """Constant-time comparison to prevent timing attacks."""
    return secrets.compare_digest(plain_password, expected_password)


def verify_username(username: str, expected_username: str) -> bool:
    """Constant-time comparison for username."""
    return secrets.compare_digest(username, expected_username)


async def get_current_admin(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_scheme),
) -> str:
    """Dependency to protect API routes with JWT bearer token."""
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authentication token. Please log in.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token = credentials.credentials
    settings = get_settings()
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=["HS256"])
        sub: str = payload.get("sub")
        if not sub:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return sub
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )
