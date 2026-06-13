"""
src/api/auth/websocket.py

ACTION 3 — SEC-007: Authenticated WebSocket endpoint.
Validates single-use ticket on handshake before allowing connection.
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query, status
from loguru import logger

from src.api.auth.token_store import TokenStore

router = APIRouter(tags=["websocket"])
token_store = TokenStore()


@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    ticket: str = Query(..., description="Single-use WS authentication ticket")
) -> None:
    """
    SEC-007: WebSocket connection requires a valid, unexpired, single-use ticket.
    Ticket is consumed on first connection — replay attempts are rejected.
    """
    # Validate ticket BEFORE accepting connection
    user_id = await token_store.consume_ws_ticket(ticket)

    if not user_id:
        logger.warning(f"WS rejected — invalid/expired ticket | ip={websocket.client.host}")
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    await websocket.accept()
    logger.info(f"WS connected | user={user_id} | ip={websocket.client.host}")

    try:
        while True:
            data = await websocket.receive_json()
            message_type = data.get("type")

            if message_type == "ping":
                await websocket.send_json({"type": "pong"})

            elif message_type == "stream_request":
                # Route to chat handler
                await websocket.send_json({
                    "type": "stream_chunk",
                    "content": "",
                    "done": False
                })

    except WebSocketDisconnect:
        logger.info(f"WS disconnected | user={user_id}")
    except Exception as e:
        logger.error(f"WS error | user={user_id} | error={e}")
        await websocket.close(code=status.WS_1011_INTERNAL_ERROR)
