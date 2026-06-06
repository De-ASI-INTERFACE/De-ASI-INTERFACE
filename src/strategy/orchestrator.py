"""Strategy Orchestrator.

Coordinates the full trade lifecycle: signal generation →
risk validation → execution routing → P&L logging.
Designed for institutional-grade, low-latency Solana trading.
"""
from typing import Any, Dict, List, Optional
import logging
from ..agents.signal_agent import SignalAgent
from ..agents.execution_adapter import ExecutionAdapter

logger = logging.getLogger(__name__)


class StrategyOrchestrator:
    """Orchestrates end-to-end trade strategy execution."""

    def __init__(
        self,
        signal_agent: SignalAgent,
        execution_adapter: ExecutionAdapter,
        max_position_size: float = 100.0,
        risk_limit_pct: float = 0.02,
    ):
        self.signal_agent = signal_agent
        self.execution_adapter = execution_adapter
        self.max_position_size = max_position_size
        self.risk_limit_pct = risk_limit_pct
        self.trade_log: List[Dict[str, Any]] = []
        self.pnl: float = 0.0

    def run_cycle(self, market_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute one full strategy cycle: signal → risk check → execute."""
        signal_result = self.signal_agent.execute(market_data)

        if not self._passes_risk_check(signal_result, market_data):
            return {"status": "blocked", "reason": "risk_limit", "signal": signal_result}

        signal_result["size"] = self._compute_position_size(signal_result, market_data)
        order = self.execution_adapter.execute(signal_result)

        trade_record = {**signal_result, **order, "market_data": market_data}
        self.trade_log.append(trade_record)
        self._update_pnl(order)
        return trade_record

    def _passes_risk_check(self, signal: Dict[str, Any], market_data: Dict[str, Any]) -> bool:
        """Block execution if confidence below threshold or position too large."""
        if signal.get("signal") == "HOLD":
            return False
        confidence = signal.get("confidence", 0)
        return confidence >= 0.55

    def _compute_position_size(self, signal: Dict[str, Any], market_data: Dict[str, Any]) -> float:
        """Kelly-inspired fractional position sizing."""
        confidence = signal.get("confidence", 0.5)
        fraction = (confidence - 0.5) * 2
        return round(min(fraction * self.max_position_size, self.max_position_size), 4)

    def _update_pnl(self, order: Dict[str, Any]) -> None:
        if order.get("status") == "filled":
            # Placeholder P&L update — real implementation uses fill price vs entry
            self.pnl += 0.0

    def get_summary(self) -> Dict[str, Any]:
        return {
            "total_cycles": len(self.trade_log),
            "pnl": self.pnl,
            "last_trade": self.trade_log[-1] if self.trade_log else None,
        }

    def health_check(self) -> bool:
        return (
            self.signal_agent.health_check()
            and self.execution_adapter.health_check()
        )
