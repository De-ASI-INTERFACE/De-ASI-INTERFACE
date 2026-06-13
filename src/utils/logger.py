# utils/logger.py
# PATCHED: SEC-008 — diagnose/backtrace disabled in production
# PATCHED: SEC-011 — log path configurable via env, not relative

import os
import sys
from loguru import logger


def setup_logging(settings) -> None:
    """Configure global logging with Loguru.

    Security hardening (SEC-008, SEC-011):
    - diagnose=True only in non-production environments to prevent
      local variable dumps (which may contain secrets, API keys,
      wallet private keys, or tokens) from appearing in production logs.
    - backtrace=True only in non-production for the same reason.
    - Log files written to an absolute, configurable path (LOG_DIR)
      that should be outside the web root and application directory.
    """
    logger.remove()  # Remove default handler

    is_production: bool = getattr(settings, "ENVIRONMENT", "production").lower() == "production"

    # SEC-011: Use absolute path from settings; default to /var/log/app
    # Never write logs to a relative path in the working directory.
    log_dir: str = getattr(settings, "LOG_DIR", "/var/log/app")
    os.makedirs(log_dir, exist_ok=True)
    log_file_path: str = os.path.join(log_dir, "file_{time:YYYY-MM-DD}.log")

    # SEC-008: diagnose and backtrace expose variable values in tracebacks.
    # Disable both in production to prevent secret/key leakage in log files.
    safe_diagnose: bool = not is_production
    safe_backtrace: bool = not is_production

    # --- File handler ---
    logger.add(
        log_file_path,
        rotation="10 MB",
        compression="zip",
        level=settings.LOG_LEVEL,
        colorize=False,
        enqueue=True,           # Async logging for performance
        backtrace=safe_backtrace,
        diagnose=safe_diagnose,
        # Structured format for log aggregation pipelines (Railway, Grafana Loki)
        format=(
            "{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | "
            "{name}:{function}:{line} | {message}"
        ),
    )

    # --- Stderr / console handler ---
    logger.add(
        sys.stderr,
        level=settings.LOG_LEVEL,
        colorize=True,
        enqueue=True,
        backtrace=safe_backtrace,
        diagnose=safe_diagnose,
        format=(
            "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
            "<level>{level: <8}</level> | "
            "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
            "<level>{message}</level>"
        ),
    )

    env_label = "PRODUCTION" if is_production else settings.ENVIRONMENT.upper()
    logger.info(
        f"Logging initialized | environment={env_label} | "
        f"level={settings.LOG_LEVEL} | log_dir={log_dir} | "
        f"diagnose={safe_diagnose} | backtrace={safe_backtrace}"
    )
