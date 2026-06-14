"""
api/index.py

Owner/Creator: Richard Patterson
© 2026 Richard Patterson. All Rights Reserved.

Vercel ASGI entry point for De-ASI-INTERFACE FastAPI application.

Vercel's Python runtime requires the ASGI app to be exported as `app`
from a file inside the /api directory. This module imports the fully
configured FastAPI application from src/main.py and re-exports it.

Architecture note on WebSockets:
  Vercel Serverless Functions do not support persistent WebSocket
  connections (functions are stateless and time-limited to 10s on
  Hobby, 60s on Pro). The /ws endpoint will return 501 on Vercel.
  For full WebSocket support, use the Railway deployment instead.
  See: DEPLOYMENT.md

All stateless HTTP endpoints (/api/auth/*, /health, /static) work
fully on Vercel via the ASGI adapter.
"""

import sys
import os

# Ensure project root is on the Python path so src.* imports resolve
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.main import app  # noqa: E402 — path manipulation must come first

# Vercel expects the ASGI app exported as `app` at module level
__all__ = ["app"]
