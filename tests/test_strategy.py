"""Unit tests for Strategy Orchestration and Monitoring."""
import pytest
from src.agents.signal_agent import SignalAgent
from src.agents.execution_adapter import ExecutionAdapter
from src.strategy.orchestrator import StrategyOrchestrator
from src.strategy.monitor import StrategyMonitor


def make_orchestrator(venue="paper"):
    sig = SignalAgent("orch-signal")
    sig.start()
    exe = ExecutionAdapter("orch-exec", venue=venue)
    exe.start()
    return StrategyOrchestrator(sig, exe, max_position_size=100.0)


class TestStrategyOrchestrator:
    def setup_method(self):
        self.orch = make_orchestrator()

    def test_health_check(self):
        assert self.orch.health_check() is True

    def test_hold_cycle_blocked(self):
        result = self.orch.run_cycle({"price": 100.0, "rsi": 50.0, "momentum": 0.0})
        assert result["status"] == "blocked"

    def test_buy_cycle_executes(self):
        result = self.orch.run_cycle({"price": 50.0, "rsi": 25.0, "momentum": 0.05})
        assert result.get("signal") == "BUY"
        assert result.get("status") == "filled"

    def test_sell_cycle_executes(self):
        result = self.orch.run_cycle({"price": 200.0, "rsi": 75.0, "momentum": -0.05})
        assert result.get("signal") == "SELL"
        assert result.get("status") == "filled"

    def test_trade_log_grows(self):
        self.orch.run_cycle({"price": 50.0, "rsi": 25.0, "momentum": 0.05})
        self.orch.run_cycle({"price": 50.0, "rsi": 25.0, "momentum": 0.05})
        assert len(self.orch.trade_log) == 2

    def test_position_size_nonzero_on_buy(self):
        result = self.orch.run_cycle({"price": 50.0, "rsi": 25.0, "momentum": 0.05})
        assert result.get("size", 0) > 0

    def test_get_summary(self):
        self.orch.run_cycle({"price": 50.0, "rsi": 25.0, "momentum": 0.05})
        summary = self.orch.get_summary()
        assert summary["total_cycles"] >= 1
        assert "pnl" in summary


class TestStrategyMonitor:
    def setup_method(self):
        self.monitor = StrategyMonitor("test_strategy")

    def test_health_check(self):
        assert self.monitor.health_check() is True

    def test_initial_metrics_zero(self):
        metrics = self.monitor.get_metrics()
        assert metrics["cycles"] == 0
        assert metrics["signals_buy"] == 0

    def test_record_buy_signal(self):
        self.monitor.record_cycle({"signal": "BUY", "status": "filled"})
        metrics = self.monitor.get_metrics()
        assert metrics["signals_buy"] == 1
        assert metrics["orders_filled"] == 1
        assert metrics["cycles"] == 1

    def test_record_sell_signal(self):
        self.monitor.record_cycle({"signal": "SELL", "status": "filled"})
        metrics = self.monitor.get_metrics()
        assert metrics["signals_sell"] == 1

    def test_record_blocked_cycle(self):
        self.monitor.record_cycle({"signal": "HOLD", "status": "blocked"})
        metrics = self.monitor.get_metrics()
        assert metrics["risk_blocked"] == 1
        assert metrics["signals_hold"] == 1

    def test_prometheus_export_format(self):
        self.monitor.record_cycle({"signal": "BUY", "status": "filled"})
        output = self.monitor.prometheus_export()
        assert "deasi_test_strategy_cycles" in output
        assert "# TYPE" in output

    def test_reset_clears_counters(self):
        self.monitor.record_cycle({"signal": "BUY", "status": "filled"})
        self.monitor.reset()
        metrics = self.monitor.get_metrics()
        assert metrics["cycles"] == 0
        assert metrics["signals_buy"] == 0

    def test_uptime_increases(self):
        import time
        time.sleep(0.01)
        metrics = self.monitor.get_metrics()
        assert metrics["uptime_seconds"] > 0
