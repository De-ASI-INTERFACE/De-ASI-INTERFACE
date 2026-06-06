"""Execution Adapter — routes validated trade signals to execution venues.
Owner/Creator: Richard Patterson
© 2026 Richard Patterson. All Rights Reserved.
"""
from typing import Any, Dict, List
import logging
from .base_agent import BaseAgent

logger = logging.getLogger(__name__)

SUPPORTED_VENUES = frozenset({"solana_dex", "cex_maker", "paper"})


class ExecutionAdapter(BaseAgent):
    """Routes signals to paper / Solana DEX / CEX maker venues."""

    def __init__(self, agent_id: str, venue: str = "paper",
                 slippage_bps: int = 30):
        super().__init__(agent_id)
        if venue not in SUPPORTED_VENUES:
            raise ValueError(
                f"Unsupported venue '{venue}'. Choose from {SUPPORTED_VENUES}")
        self.venue        = venue
        self.slippage_bps = slippage_bps
        self.order_log: List[Dict[str, Any]] = []

    def execute(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        if not self._running:
            raise RuntimeError(
                f"ExecutionAdapter {self.agent_id} is not running.")
        signal = payload.get("signal")
        price  = payload.get("price", 0.0)
        size   = payload.get("size", 1.0)
        if signal not in {"BUY", "SELL"}:
            return {"status": "skipped",
                    "reason": f"Signal '{signal}' requires no execution."}
        slip = self.slippage_bps / 10_000
        eff  = price * (1 + slip) if signal == "BUY" else price * (1 - slip)
        order = {
            "venue": self.venue, "signal": signal,
            "requested_price": price,
            "effective_price": round(eff, 6),
            "size": size,
            "status": "filled" if self.venue == "paper" else "pending",
        }
        self.order_log.append(order)
        return order

    def health_check(self) -> bool:
        return self._running and self.venue in SUPPORTED_VENUES
