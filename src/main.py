"""
src/main.py

Owner/Creator: Richard Patterson
© 2026 Richard Patterson. All Rights Reserved.

Production entry point for De-ASI-INTERFACE.

Wires up (in startup order):
  1. Loguru logging          (SEC-008, SEC-011)
  2. PostgreSQL pool         (asyncpg, min=2, max=10)
  3. Redis client            (aioredis — token store, rate limiter, TOTP replay)
  4. FastAPI app + CORS      (locked to CORS_ORIGINS)
  5. Auth routers            (SEC-001, 004, 005, 007, 010)
  6. WebSocket router        (SEC-007)
  7. Static file serving     (src/static/)
  8. Health + root endpoints
"""

import os
from contextlib import asynccontextmanager
from typing import AsyncGenerator, Optional

import aioredis
import asyncpg
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from loguru import logger

from config import settings
from src.api.auth import auth_router, ws_router
from src.api.auth.user_store import close_db_pool, init_db_pool
from src.utils.logger import setup_logging


# ---------------------------------------------------------------------------
# Logging bootstrap — must happen before any other import side-effects
# ---------------------------------------------------------------------------
setup_logging(settings)


# ---------------------------------------------------------------------------
# Shared infrastructure clients (injected into routers via app.state)
# ---------------------------------------------------------------------------
redis_client: Optional[aioredis.Redis] = None
db_pool: Optional[asyncpg.Pool] = None


# ---------------------------------------------------------------------------
# Lifespan — startup / shutdown in strict dependency order
# ---------------------------------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    global redis_client, db_pool

    logger.info("=" * 60)
    logger.info("De-ASI-INTERFACE starting up")
    logger.info(f"  Environment : {settings.ENVIRONMENT}")
    logger.info(f"  Log level   : {settings.LOG_LEVEL}")
    logger.info(f"  Log dir     : {settings.LOG_DIR}")
    logger.info(f"  Host        : {settings.HOST}:{settings.PORT}")
    logger.info("=" * 60)

    # ------------------------------------------------------------------
    # 1. PostgreSQL connection pool
    # ------------------------------------------------------------------
    try:
        await init_db_pool()
        db_pool = True  # pool lives inside user_store module
        logger.info("PostgreSQL pool ready")
    except Exception as e:
        logger.critical(f"PostgreSQL pool FAILED: {e}")
        if settings.ENVIRONMENT == "production":
            raise  # Hard fail in production — no DB = no app
        logger.warning("Continuing without DB (development mode)")

    # ------------------------------------------------------------------
    # 2. Redis client
    # ------------------------------------------------------------------
    try:
        redis_client = aioredis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True,
            socket_connect_timeout=5,
            socket_timeout=5,
            retry_on_timeout=True,
            health_check_interval=30,
        )
        await redis_client.ping()
        logger.info(f"Redis ready | url={settings.REDIS_URL.split('@')[-1]}")
    except Exception as e:
        logger.error(f"Redis connection FAILED: {e}")
        if settings.ENVIRONMENT == "production":
            raise  # Hard fail — Redis required for token revocation + rate limiting
        logger.warning("Continuing with in-memory fallback (development only)")
        redis_client = None

    # ------------------------------------------------------------------
    # 3. Inject clients into app.state so routers can access them
    # ------------------------------------------------------------------
    app.state.redis = redis_client
    logger.info("Infrastructure ready — serving requests")

    yield  # App is live

    # ------------------------------------------------------------------
    # SHUTDOWN — reverse order
    # ------------------------------------------------------------------
    logger.info("De-ASI-INTERFACE shutting down ...")
    if redis_client:
        await redis_client.close()
        logger.info("Redis connection closed")
    await close_db_pool()
    logger.info("PostgreSQL pool closed")
    logger.info("Shutdown complete")


# ---------------------------------------------------------------------------
# FastAPI application
# ---------------------------------------------------------------------------
app = FastAPI(
    title="De-ASI-INTERFACE",
    description="Production-hardened ASI interface API — SEC-001 through SEC-014 patched",
    version="1.0.0-secure",
    # Disable docs in production — never expose OpenAPI schema publicly
    docs_url="/api/docs"            if settings.ENVIRONMENT != "production" else None,
    redoc_url="/api/redoc"          if settings.ENVIRONMENT != "production" else None,
    openapi_url="/api/openapi.json" if settings.ENVIRONMENT != "production" else None,
    lifespan=lifespan,
)


# ---------------------------------------------------------------------------
# CORS middleware — strict, credentials-aware
# ---------------------------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in settings.CORS_ORIGINS.split(",")],
    allow_credentials=True,          # Required for httpOnly cookie auth (SEC-001)
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type", "X-CSRF-Token"],
    expose_headers=[],
    max_age=600,
)


# ---------------------------------------------------------------------------
# Router registration
# ---------------------------------------------------------------------------
app.include_router(auth_router)      # /api/auth/login, /verify-2fa, /csrf-token, /ws-ticket, /logout
app.include_router(ws_router)        # /ws


# ---------------------------------------------------------------------------
# Static files
# ---------------------------------------------------------------------------
if os.path.exists("src/static"):
    app.mount("/static", StaticFiles(directory="src/static"), name="static")
    logger.info("Static files mounted at /static")


# ---------------------------------------------------------------------------
# Health check — checks all infrastructure dependencies
# ---------------------------------------------------------------------------
@app.get("/health", tags=["ops"])
async def health_check() -> dict:
    """
    Deep health check. Verifies:
      - Redis connectivity (ping)
      - PostgreSQL connectivity (pool stats)
    Returns 200 always — status field indicates real health.
    Monitoring systems should alert on redis != 'connected' or db != 'connected'.
    """
    from src.api.auth.user_store import _pool as _db_pool

    # Redis health
    redis_status = "disconnected"
    if app.state.redis:
        try:
            await app.state.redis.ping()
            redis_status = "connected"
        except Exception:
            redis_status = "error"

    # DB health
    db_status = "disconnected"
    if _db_pool:
        try:
            async with _db_pool.acquire() as conn:
                await conn.fetchval("SELECT 1")
            db_status = "connected"
        except Exception:
            db_status = "error"

    return {
        "status": "ok",
        "version": "1.0.0-secure",
        "environment": settings.ENVIRONMENT,
        "redis": redis_status,
        "db": db_status,
    }


# ---------------------------------------------------------------------------
# Root — serve frontend
# ---------------------------------------------------------------------------
@app.get("/", include_in_schema=False)
async def root() -> FileResponse:
    return FileResponse("src/static/index.html")
