"""
src/api/auth/routes.py

Complete authentication backend — FastAPI implementation.

Security actions implemented:
  ACTION 1 (SEC-001) — httpOnly cookie auth on /verify-2fa
  ACTION 2 (SEC-004) — CSRF token endpoint + validation dependency
  ACTION 3 (SEC-007) — WebSocket ticket endpoint (30s TTL, Redis-backed, single-use)
  ACTION 4 (SEC-005) — 2FA rate limiting (5 attempts / 15 min per username)
  ACTION 5          — Logout with mandatory server-side token invalidation
"""

import secrets
import time
from datetime import datetime, timedelta, timezone
from typing import Optional

import jwt
from fastapi import APIRouter, Cookie, Depends, HTTPException, Request, Response, status
from fastapi.security import HTTPBearer
from pydantic import BaseModel
from loguru import logger

from src.api.auth.rate_limiter import RateLimiter
from src.api.auth.token_store import TokenStore
from src.api.auth.totp import verify_totp
from src.api.auth.user_store import authenticate_user
from config import settings

router = APIRouter(prefix="/api/auth", tags=["auth"])

# ---------------------------------------------------------------------------
# Stores (inject Redis-backed implementations in production)
# ---------------------------------------------------------------------------
token_store = TokenStore()        # Manages JWT revocation list
rate_limiter = RateLimiter()      # 2FA attempt tracking


# ---------------------------------------------------------------------------
# Pydantic models
# ---------------------------------------------------------------------------
class LoginRequest(BaseModel):
    username: str
    password: str

class Verify2FARequest(BaseModel):
    username: str
    code: str

class LogoutRequest(BaseModel):
    pass  # Auth via cookie


# ---------------------------------------------------------------------------
# ACTION 2 — SEC-004: CSRF token generation + validation
# ---------------------------------------------------------------------------
@router.get("/csrf-token")
async def get_csrf_token(response: Response) -> dict:
    """
    Issues a CSRF token as both a JSON response value (for JS to read once)
    and a SameSite=Strict cookie (for double-submit validation).
    """
    token = secrets.token_hex(32)
    response.set_cookie(
        key="csrf_token",
        value=token,
        httponly=False,          # Must be readable by JS for the header
        secure=True,
        samesite="strict",
        max_age=3600,
        path="/"
    )
    return {"csrf_token": token}


def validate_csrf(request: Request, csrf_token: Optional[str] = Cookie(default=None)) -> None:
    """
    FastAPI dependency — validates X-CSRF-Token header against cookie value.
    Raises 403 if missing or mismatched.
    """
    header_token = request.headers.get("X-CSRF-Token")
    if not header_token or not csrf_token:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="CSRF token missing"
        )
    if not secrets.compare_digest(header_token, csrf_token):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="CSRF token invalid"
        )


# ---------------------------------------------------------------------------
# Login — initiates 2FA flow
# ---------------------------------------------------------------------------
@router.post("/login")
async def login(
    request_body: LoginRequest,
    request: Request,
    _csrf: None = Depends(validate_csrf)
) -> dict:
    user = await authenticate_user(request_body.username, request_body.password)
    if not user:
        # Constant-time response to prevent user enumeration
        await asyncio.sleep(0.5)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )

    logger.info(f"Login initiated | user={request_body.username} | ip={request.client.host}")
    return {"success": True, "require_2fa": True}


# ---------------------------------------------------------------------------
# ACTION 1 (SEC-001) + ACTION 4 (SEC-005)
# verify-2fa: rate-limited + httpOnly cookie on success
# ---------------------------------------------------------------------------
@router.post("/verify-2fa")
async def verify_2fa(
    request_body: Verify2FARequest,
    request: Request,
    response: Response,
    _csrf: None = Depends(validate_csrf)
) -> dict:
    """
    ACTION 4 — SEC-005: Rate limit 2FA to 5 attempts per 15 minutes per username.
    ACTION 1 — SEC-001: On success, set auth token as httpOnly cookie.
                        Never return token in JSON response body.
    """
    username = request_body.username
    ip = request.client.host

    # ACTION 4: Check rate limit before any processing
    attempt_key = f"2fa:{username}"
    if not await rate_limiter.check(attempt_key, max_attempts=5, window_seconds=900):
        logger.warning(f"2FA rate limit exceeded | user={username} | ip={ip}")
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many attempts. Account temporarily locked. Try again in 15 minutes."
        )

    # Validate TOTP code
    is_valid = await verify_totp(username, request_body.code)
    if not is_valid:
        await rate_limiter.record_failure(attempt_key)
        remaining = await rate_limiter.attempts_remaining(attempt_key, max_attempts=5)
        logger.warning(f"2FA failed | user={username} | ip={ip} | remaining_attempts={remaining}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid code. {remaining} attempts remaining."
        )

    # Reset rate limiter on success
    await rate_limiter.reset(attempt_key)

    # Generate JWT
    now = datetime.now(timezone.utc)
    payload = {
        "sub": username,
        "iat": now,
        "exp": now + timedelta(hours=1),
        "jti": secrets.token_hex(16)  # Unique token ID for revocation
    }
    token = jwt.encode(payload, settings.JWT_SECRET, algorithm="HS256")

    # Store JTI for revocation tracking
    await token_store.store(payload["jti"], ttl_seconds=3600)

    # ACTION 1 — SEC-001: Set httpOnly cookie — NEVER return token in body
    response.set_cookie(
        key="auth_token",
        value=token,
        httponly=True,           # Not accessible from JavaScript
        secure=True,             # HTTPS only
        samesite="strict",       # CSRF protection layer 2
        max_age=3600,            # 1 hour
        path="/"
    )

    logger.info(f"2FA success | user={username} | ip={ip} | jti={payload['jti'][:8]}...")
    return {"success": True}    # NO token in response body


# ---------------------------------------------------------------------------
# ACTION 3 — SEC-007: WebSocket ticket endpoint
# ---------------------------------------------------------------------------
@router.post("/ws-ticket")
async def get_ws_ticket(
    request: Request,
    _csrf: None = Depends(validate_csrf),
    auth_token: Optional[str] = Cookie(default=None)
) -> dict:
    """
    ACTION 3 — SEC-007: Issues a short-lived (30s), single-use WebSocket ticket.
    The ticket is stored in Redis and consumed on WS handshake.
    This avoids putting the JWT in a URL query parameter.
    """
    if not auth_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")

    # Validate the auth cookie JWT
    try:
        payload = jwt.decode(auth_token, settings.JWT_SECRET, algorithms=["HS256"])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Session expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    # Verify JTI not revoked
    if not await token_store.is_valid(payload["jti"]):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token revoked")

    # Issue single-use WS ticket with 30s TTL
    ticket = secrets.token_urlsafe(32)
    await token_store.store_ws_ticket(ticket, user_id=payload["sub"], ttl_seconds=30)

    logger.info(f"WS ticket issued | user={payload['sub']} | ip={request.client.host}")
    return {"ticket": ticket}


# ---------------------------------------------------------------------------
# ACTION 5 — SEC-010: Logout with mandatory server-side token invalidation
# ---------------------------------------------------------------------------
@router.post("/logout")
async def logout(
    request: Request,
    response: Response,
    _csrf: None = Depends(validate_csrf),
    auth_token: Optional[str] = Cookie(default=None)
) -> dict:
    """
    ACTION 5 — SEC-010: Revokes the JWT server-side before clearing the cookie.
    If revocation fails, returns 500 so the client knows to force re-auth.
    """
    if auth_token:
        try:
            payload = jwt.decode(
                auth_token,
                settings.JWT_SECRET,
                algorithms=["HS256"],
                options={"verify_exp": False}  # Allow revoking expired tokens too
            )
            await token_store.revoke(payload["jti"])
            logger.info(f"Logout | user={payload['sub']} | jti={payload['jti'][:8]}... | revoked=True")
        except Exception as e:
            logger.error(f"Logout revocation failed: {e}")
            # Return error so client knows server-side invalidation failed
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Logout failed server-side. Please contact support."
            )

    # Clear the auth cookie
    response.delete_cookie(key="auth_token", path="/", secure=True, samesite="strict")
    response.delete_cookie(key="csrf_token", path="/", samesite="strict")

    return {"success": True}
