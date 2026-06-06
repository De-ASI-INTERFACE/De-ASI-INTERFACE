"""Strategy Orchestrator — full trade lifecycle.
Owner/Creator: Richard Patterson
© 2026 Richard Patterson. All Rights Reserved.
"""
from typing import Any, Dict, List
import logging
from ..agents.signal_agent import SignalAgent
from ..agents.execution_adapter import ExecutionAdapter

logger = logging.getLogger(__name__)


class StrategyOrchestrator:
    MIN_CONFIDENCE = 0.55

    def __init__(self, signal_agent: SignalAgent,
                 execution_adapter: ExecutionAdapter,
                 max_position_size: float = 100.0,
                 risk_limit_pct: float = 0.02):
        self.signal_agent      = signal_agent
        self.execution_adapter = execution_adapter
        self.max_position_size = max_position_size
        self.risk_limit_pct    = risk_limit_pct
        self.trade_log: List[Dict[str, Any]] = []
        self.pnl: float = 0.0

    def run_cycle(self, market_data: Dict[str, Any]) -> Dict[str, Any]:
        sig = self.signal_agent.execute(market_data)
        if sig.get("signal") == "HOLD" or \
           sig.get("confidence", 0) < self.MIN_CONFIDENCE:
            return {"status": "blocked", "reason": "risk_limit", "signal": sig}
        sig["size"] = self._position_size(sig)
        order = self.execution_adapter.execute(sig)
        record = {**sig, **order, "market_data": market_data}
        self.trade_log.append(record)
        return record

    def _position_size(self, sig: Dict[str, Any]) -> float:
        conf = sig.get("confidence", 0.5)
        frac = (conf - 0.5) * 2
        return round(min(frac * self.max_position_size,
                         self.max_position_size), 4)

    def get_summary(self) -> Dict[str, Any]:
        return {"total_cycles": len(self.trade_log), "pnl": self.pnl,
                "last_trade": self.trade_log[-1] if self.trade_log else None}

    def health_check(self) -> bool:
        return (self.signal_agent.health_check() and
                self.execution_adapter.health_check())
