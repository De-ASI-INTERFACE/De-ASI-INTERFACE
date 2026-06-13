"""
src/main.py

Production entry point for De-ASI-INTERFACE.

Wires up:
  - FastAPI application with CORS
  - Auth routers (SEC-001, 004, 005, 007, 010)
  - WebSocket router (SEC-007)
  - Redis-backed TokenStore + RateLimiter
  - Loguru logging (SEC-008, SEC-011)
  - Health check endpoint
"""

import asyncio
import os
from contextlib import asynccontextmanager
from typing import AsyncGenerator

import aioredis
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from loguru import logger

from config import settings
from src.api.auth import auth_router, ws_router
from src.utils.logger import setup_logging


# ---------------------------------------------------------------------------
# Logging bootstrap (must happen before anything else)
# ---------------------------------------------------------------------------
setup_logging(settings)


# ---------------------------------------------------------------------------
# Redis client (module-level, shared across app)
# ---------------------------------------------------------------------------
redis_client: aioredis.Redis | None = None


# ---------------------------------------------------------------------------
# Lifespan context (replaces deprecated @app.on_event)
# ---------------------------------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Manage startup and shutdown lifecycle."""
    global redis_client

    # ---- STARTUP ----
    logger.info("De-ASI-INTERFACE starting up ...")
    logger.info(f"Environment : {settings.ENVIRONMENT}")
    logger.info(f"Log level   : {settings.LOG_LEVEL}")
    logger.info(f"Log dir     : {settings.LOG_DIR}")

    try:
        redis_client = aioredis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True,
            socket_connect_timeout=5,
            socket_timeout=5,
        )
        await redis_client.ping()
        logger.info(f"Redis connected | url={settings.REDIS_URL}")
    except Exception as e:
        logger.error(f"Redis connection failed: {e}")
        logger.warning("Running with in-memory token store (not suitable for production)")
        redis_client = None

    yield

    # ---- SHUTDOWN ----
    logger.info("De-ASI-INTERFACE shutting down ...")
    if redis_client:
        await redis_client.close()
        logger.info("Redis connection closed")


# ---------------------------------------------------------------------------
# FastAPI application
# ---------------------------------------------------------------------------
app = FastAPI(
    title="De-ASI-INTERFACE",
    description="Production-hardened ASI interface API — SEC-001 through SEC-014 patched",
    version="1.0.0-secure",
    docs_url="/api/docs"        if settings.ENVIRONMENT != "production" else None,
    redoc_url="/api/redoc"      if settings.ENVIRONMENT != "production" else None,
    openapi_url="/api/openapi.json" if settings.ENVIRONMENT != "production" else None,
    lifespan=lifespan,
)


# ---------------------------------------------------------------------------
# CORS middleware — locked to configured origin
# ---------------------------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in settings.CORS_ORIGINS.split(",")],
    allow_credentials=True,                      # Required for httpOnly cookie auth
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type", "X-CSRF-Token"],
    expose_headers=[],
    max_age=600,
)


# ---------------------------------------------------------------------------
# Router registration
# ---------------------------------------------------------------------------
app.include_router(auth_router)    # /api/auth/...
app.include_router(ws_router)      # /ws


# ---------------------------------------------------------------------------
# Static files (frontend)
# ---------------------------------------------------------------------------
if os.path.exists("src/static"):
    app.mount("/static", StaticFiles(directory="src/static"), name="static")
    logger.info("Static files mounted at /static")


# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------
@app.get("/health", tags=["ops"])
async def health_check() -> dict:
    """
    Deployment health check.
    Returns Redis connectivity status and app version.
    """
    redis_status = "unknown"
    if redis_client:
        try:
            await redis_client.ping()
            redis_status = "connected"
        except Exception:
            redis_status = "error"
    else:
        redis_status = "in-memory-fallback"

    return {
        "status": "ok",
        "version": "1.0.0-secure",
        "environment": settings.ENVIRONMENT,
        "redis": redis_status,
    }


# ---------------------------------------------------------------------------
# Root redirect to static index
# ---------------------------------------------------------------------------
@app.get("/", include_in_schema=False)
async def root():
    from fastapi.responses import FileResponse
    return FileResponse("src/static/index.html")
