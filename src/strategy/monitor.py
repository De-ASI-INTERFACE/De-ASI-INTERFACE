"""Real-Time Strategy Monitor.

Tracks live performance metrics, emits Prometheus-compatible
stats, and feeds Grafana dashboards via structured log output.
"""
from typing import Any, Dict, List
import time
import logging

logger = logging.getLogger(__name__)


class StrategyMonitor:
    """Collects and exposes real-time strategy performance metrics."""

    def __init__(self, strategy_id: str):
        self.strategy_id = strategy_id
        self._metrics: Dict[str, Any] = {
            "cycles": 0,
            "signals_buy": 0,
            "signals_sell": 0,
            "signals_hold": 0,
            "orders_filled": 0,
            "orders_skipped": 0,
            "risk_blocked": 0,
            "pnl_usd": 0.0,
            "uptime_seconds": 0.0,
        }
        self._start_time = time.time()
        self._events: List[Dict[str, Any]] = []

    def record_cycle(self, result: Dict[str, Any]) -> None:
        """Ingest a cycle result and update all metrics."""
        self._metrics["cycles"] += 1
        self._metrics["uptime_seconds"] = round(time.time() - self._start_time, 2)

        signal = result.get("signal", "HOLD")
        if signal == "BUY":
            self._metrics["signals_buy"] += 1
        elif signal == "SELL":
            self._metrics["signals_sell"] += 1
        else:
            self._metrics["signals_hold"] += 1

        status = result.get("status", "")
        if status == "filled":
            self._metrics["orders_filled"] += 1
        elif status == "skipped":
            self._metrics["orders_skipped"] += 1
        elif status == "blocked":
            self._metrics["risk_blocked"] += 1

        self._events.append({"ts": time.time(), **result})
        logger.info(f"[Monitor:{self.strategy_id}] Cycle {self._metrics['cycles']}: signal={signal} status={status}")

    def get_metrics(self) -> Dict[str, Any]:
        """Return current snapshot of all metrics."""
        self._metrics["uptime_seconds"] = round(time.time() - self._start_time, 2)
        return dict(self._metrics)

    def prometheus_export(self) -> str:
        """Export metrics in Prometheus text format for scraping."""
        lines = []
        for key, val in self._metrics.items():
            metric_name = f"deasi_{self.strategy_id}_{key}"
            lines.append(f"# TYPE {metric_name} gauge")
            lines.append(f"{metric_name} {val}")
        return "\n".join(lines)

    def reset(self) -> None:
        """Reset all counters (preserves uptime)."""
        start = self._start_time
        self.__init__(self.strategy_id)
        self._start_time = start

    def health_check(self) -> bool:
        return self._metrics["cycles"] >= 0
