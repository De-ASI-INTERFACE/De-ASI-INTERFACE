"""Signal Agent — RSI + momentum directional signal generator.
Owner/Creator: Richard Patterson
© 2026 Richard Patterson. All Rights Reserved.
"""
from typing import Any, Dict, List, Optional
import logging
from .base_agent import BaseAgent

logger = logging.getLogger(__name__)

_DEFAULT_THRESHOLDS = {
    "momentum": 0.02,
    "rsi_overbought": 70.0,
    "rsi_oversold": 30.0,
}


class SignalAgent(BaseAgent):
    """Generates BUY/SELL/HOLD signals with confidence scores."""

    def __init__(self, agent_id: str,
                 thresholds: Optional[Dict[str, float]] = None):
        super().__init__(agent_id)
        self.thresholds = thresholds or dict(_DEFAULT_THRESHOLDS)
        self.signal_history: List[Dict[str, Any]] = []

    def execute(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        if not self._running:
            raise RuntimeError(f"Agent {self.agent_id} is not running.")
        price = payload.get("price")
        if price is None:
            raise ValueError("Payload must contain 'price' field.")
        rsi      = payload.get("rsi")
        momentum = float(payload.get("momentum", 0.0))
        signal, confidence = "HOLD", 0.5
        if rsi is not None:
            if rsi < self.thresholds["rsi_oversold"] and momentum > 0:
                signal     = "BUY"
                confidence = round(min(0.5 + abs(momentum) * 10, 0.99), 4)
            elif rsi > self.thresholds["rsi_overbought"] and momentum < 0:
                signal     = "SELL"
                confidence = round(min(0.5 + abs(momentum) * 10, 0.99), 4)
        result = {"agent_id": self.agent_id, "signal": signal,
                  "confidence": confidence, "price": price, "rsi": rsi}
        self.signal_history.append(result)
        return result

    def health_check(self) -> bool:
        return self._running

    def get_last_signal(self) -> Optional[Dict[str, Any]]:
        return self.signal_history[-1] if self.signal_history else None
