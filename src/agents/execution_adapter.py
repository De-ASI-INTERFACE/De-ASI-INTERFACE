"""Execution Adapter — routes signals to on-chain or CEX execution.

Bridges the SignalAgent output to Solana DEX or centralized
exchange order placement logic.
"""
from typing import Any, Dict, Optional
import logging
from .base_agent import BaseAgent

logger = logging.getLogger(__name__)


class ExecutionAdapter(BaseAgent):
    """Routes validated trade signals to execution venues."""

    SUPPORTED_VENUES = {"solana_dex", "cex_maker", "paper"}

    def __init__(self, agent_id: str, venue: str = "paper", slippage_bps: int = 30):
        super().__init__(agent_id)
        if venue not in self.SUPPORTED_VENUES:
            raise ValueError(f"Unsupported venue '{venue}'. Choose from {self.SUPPORTED_VENUES}")
        self.venue = venue
        self.slippage_bps = slippage_bps
        self.order_log: list = []

    def execute(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a trade signal at the configured venue."""
        if not self._running:
            raise RuntimeError(f"ExecutionAdapter {self.agent_id} is not running.")

        signal = payload.get("signal")
        price = payload.get("price")
        size = payload.get("size", 1.0)

        if signal not in {"BUY", "SELL"}:
            return {"status": "skipped", "reason": f"Signal '{signal}' requires no execution."}

        effective_price = price * (1 + self.slippage_bps / 10000) if signal == "BUY" else price * (1 - self.slippage_bps / 10000)

        order = {
            "venue": self.venue,
            "signal": signal,
            "requested_price": price,
            "effective_price": round(effective_price, 6),
            "size": size,
            "status": "filled" if self.venue == "paper" else "pending",
        }
        self.order_log.append(order)
        logger.info(f"Order routed via {self.venue}: {order}")
        return order

    def health_check(self) -> bool:
        return self._running and self.venue in self.SUPPORTED_VENUES
