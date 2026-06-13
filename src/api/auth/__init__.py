from src.api.auth.routes import router as auth_router
from src.api.auth.websocket import router as ws_router

__all__ = ["auth_router", "ws_router"]
