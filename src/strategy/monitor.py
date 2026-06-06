"""Real-Time Strategy Monitor — Prometheus-compatible metrics.
Owner/Creator: Richard Patterson
© 2026 Richard Patterson. All Rights Reserved.
"""
from typing import Any, Dict, List
import time, logging

logger = logging.getLogger(__name__)


class StrategyMonitor:
    def __init__(self, strategy_id: str):
        self.strategy_id = strategy_id
        self._start      = time.time()
        self._metrics: Dict[str, Any] = {
            "cycles": 0, "signals_buy": 0, "signals_sell": 0,
            "signals_hold": 0, "orders_filled": 0, "orders_skipped": 0,
            "risk_blocked": 0, "pnl_usd": 0.0, "uptime_seconds": 0.0,
        }
        self._events: List[Dict[str, Any]] = []

    def record_cycle(self, result: Dict[str, Any]) -> None:
        self._metrics["cycles"] += 1
        self._metrics["uptime_seconds"] = round(time.time() - self._start, 3)
        sig    = result.get("signal", "HOLD")
        status = result.get("status", "")
        if sig == "BUY":    self._metrics["signals_buy"]  += 1
        elif sig == "SELL": self._metrics["signals_sell"] += 1
        else:               self._metrics["signals_hold"] += 1
        if status == "filled":   self._metrics["orders_filled"]  += 1
        elif status == "skipped":self._metrics["orders_skipped"] += 1
        elif status == "blocked":self._metrics["risk_blocked"]   += 1
        self._events.append({"ts": time.time(), **result})

    def get_metrics(self) -> Dict[str, Any]:
        self._metrics["uptime_seconds"] = round(time.time() - self._start, 3)
        return dict(self._metrics)

    def prometheus_export(self) -> str:
        lines = []
        for k, v in self._metrics.items():
            name = f"deasi_{self.strategy_id}_{k}"
            lines += [f"# TYPE {name} gauge", f"{name} {v}"]
        return "\n".join(lines)

    def reset(self) -> None:
        start = self._start
        self.__init__(self.strategy_id)
        self._start = start

    def health_check(self) -> bool:
        return self._metrics["cycles"] >= 0
