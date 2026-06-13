"""
config.py

Owner/Creator: Richard Patterson
© 2026 Richard Patterson. All Rights Reserved.

Centralized application configuration via environment variables.

All secrets and environment-specific values are loaded from the environment.
Never hardcode credentials here. Use .env.railway as a reference for
required variables in Railway: Project -> Variables.

Security gates implemented:
  SEC-008 : diagnose/backtrace disabled in production (gated on ENVIRONMENT)
  SEC-011 : LOG_DIR forces absolute log path
"""

import os
from dataclasses import dataclass, field


@dataclass
class Settings:
    """Application settings loaded from environment variables."""

    # -----------------------------------------------------------------------
    # Core environment
    # -----------------------------------------------------------------------
    # SEC-008: Must be 'production' in Railway to disable diagnose/backtrace
    ENVIRONMENT: str = field(
        default_factory=lambda: os.getenv("ENVIRONMENT", "development")
    )

    # -----------------------------------------------------------------------
    # Logging (SEC-008, SEC-011)
    # -----------------------------------------------------------------------
    LOG_LEVEL: str = field(
        default_factory=lambda: os.getenv("LOG_LEVEL", "DEBUG")
    )
    # SEC-011: Absolute path — never use a relative path in production
    LOG_DIR: str = field(
        default_factory=lambda: os.getenv("LOG_DIR", "/var/log/app")
    )

    # -----------------------------------------------------------------------
    # Database — REQUIRED in production
    # Railway auto-provides DATABASE_URL when Postgres plugin is added
    # -----------------------------------------------------------------------
    DATABASE_URL: str = field(
        default_factory=lambda: os.getenv(
            "DATABASE_URL",
            "postgresql://localhost:5432/deasiinterface_dev"
        )
    )

    # -----------------------------------------------------------------------
    # Redis — REQUIRED in production for:
    #   - JWT JTI revocation list (SEC-010)
    #   - 2FA rate limiter persistence (SEC-005)
    #   - WebSocket ticket store (SEC-007)
    # Railway auto-provides REDIS_URL when Redis plugin is added
    # -----------------------------------------------------------------------
    REDIS_URL: str = field(
        default_factory=lambda: os.getenv("REDIS_URL", "redis://localhost:6379/0")
    )

    # -----------------------------------------------------------------------
    # Authentication (SEC-001, SEC-004, SEC-005, SEC-010)
    # REQUIRED: 64-char random hex — generate with:
    #   python -c "import secrets; print(secrets.token_hex(64))"
    # -----------------------------------------------------------------------
    JWT_SECRET: str = field(
        default_factory=lambda: os.getenv("JWT_SECRET", "INSECURE-DEV-ONLY-CHANGE-ME")
    )
    JWT_EXPIRY_HOURS: int = field(
        default_factory=lambda: int(os.getenv("JWT_EXPIRY_HOURS", "1"))
    )

    # -----------------------------------------------------------------------
    # CORS — Lock to your Railway deployment domain
    # -----------------------------------------------------------------------
    CORS_ORIGINS: str = field(
        default_factory=lambda: os.getenv(
            "CORS_ORIGINS",
            "http://localhost:3000,http://localhost:8000"
        )
    )

    # -----------------------------------------------------------------------
    # App server
    # -----------------------------------------------------------------------
    PORT: int = field(
        default_factory=lambda: int(os.getenv("PORT", "8000"))
    )
    HOST: str = field(
        default_factory=lambda: os.getenv("HOST", "0.0.0.0")
    )

    def __post_init__(self) -> None:
        """Validate critical settings on startup — raises on misconfiguration."""
        if self.ENVIRONMENT == "production":
            if self.JWT_SECRET == "INSECURE-DEV-ONLY-CHANGE-ME":
                raise ValueError(
                    "CRITICAL: JWT_SECRET must be set to a secure random value in production. "
                    "Generate with: python -c \"import secrets; print(secrets.token_hex(64))\""
                )
            if "localhost" in self.DATABASE_URL:
                raise ValueError(
                    "CRITICAL: DATABASE_URL points to localhost in production. "
                    "Set DATABASE_URL to your Railway PostgreSQL connection string."
                )
            if "localhost" in self.REDIS_URL:
                raise ValueError(
                    "CRITICAL: REDIS_URL points to localhost in production. "
                    "Set REDIS_URL to your Railway Redis connection string."
                )
            if "localhost" in self.CORS_ORIGINS:
                import warnings
                warnings.warn(
                    "WARNING: CORS_ORIGINS contains localhost in production environment.",
                    stacklevel=2
                )


# Singleton instance — imported everywhere
settings = Settings()
