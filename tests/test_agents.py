"""Unit tests for AI Agent Execution Adapters."""
import pytest
from src.agents.base_agent import BaseAgent
from src.agents.signal_agent import SignalAgent
from src.agents.execution_adapter import ExecutionAdapter


# --- SignalAgent Tests ---

class TestSignalAgent:
    def setup_method(self):
        self.agent = SignalAgent("test-signal-001")
        self.agent.start()

    def test_initialization(self):
        assert self.agent.agent_id == "test-signal-001"
        assert self.agent.is_running is True

    def test_health_check_running(self):
        assert self.agent.health_check() is True

    def test_health_check_stopped(self):
        self.agent.stop()
        assert self.agent.health_check() is False

    def test_hold_signal_neutral_rsi(self):
        result = self.agent.execute({"price": 100.0, "rsi": 50.0, "momentum": 0.0})
        assert result["signal"] == "HOLD"
        assert result["price"] == 100.0

    def test_buy_signal_oversold(self):
        result = self.agent.execute({"price": 50.0, "rsi": 25.0, "momentum": 0.05})
        assert result["signal"] == "BUY"
        assert result["confidence"] > 0.5

    def test_sell_signal_overbought(self):
        result = self.agent.execute({"price": 200.0, "rsi": 75.0, "momentum": -0.05})
        assert result["signal"] == "SELL"
        assert result["confidence"] > 0.5

    def test_missing_price_raises(self):
        with pytest.raises(ValueError):
            self.agent.execute({"rsi": 50.0})

    def test_not_running_raises(self):
        self.agent.stop()
        with pytest.raises(RuntimeError):
            self.agent.execute({"price": 100.0})

    def test_signal_history_accumulates(self):
        self.agent.execute({"price": 100.0, "rsi": 50.0})
        self.agent.execute({"price": 101.0, "rsi": 50.0})
        assert len(self.agent.signal_history) == 2

    def test_get_last_signal(self):
        self.agent.execute({"price": 100.0, "rsi": 50.0})
        last = self.agent.get_last_signal()
        assert last is not None
        assert "signal" in last

    def test_get_last_signal_empty(self):
        agent = SignalAgent("empty-agent")
        agent.start()
        assert agent.get_last_signal() is None

    def test_confidence_capped_at_099(self):
        result = self.agent.execute({"price": 50.0, "rsi": 1.0, "momentum": 10.0})
        assert result["confidence"] <= 0.99


# --- ExecutionAdapter Tests ---

class TestExecutionAdapter:
    def setup_method(self):
        self.adapter = ExecutionAdapter("test-exec-001", venue="paper")
        self.adapter.start()

    def test_initialization(self):
        assert self.adapter.venue == "paper"
        assert self.adapter.slippage_bps == 30

    def test_invalid_venue_raises(self):
        with pytest.raises(ValueError):
            ExecutionAdapter("bad", venue="unknown_venue")

    def test_health_check(self):
        assert self.adapter.health_check() is True

    def test_buy_order_filled(self):
        result = self.adapter.execute({"signal": "BUY", "price": 100.0, "size": 1.0})
        assert result["status"] == "filled"
        assert result["effective_price"] > 100.0  # slippage applied

    def test_sell_order_filled(self):
        result = self.adapter.execute({"signal": "SELL", "price": 100.0, "size": 1.0})
        assert result["status"] == "filled"
        assert result["effective_price"] < 100.0  # slippage applied

    def test_hold_signal_skipped(self):
        result = self.adapter.execute({"signal": "HOLD", "price": 100.0})
        assert result["status"] == "skipped"

    def test_order_log_grows(self):
        self.adapter.execute({"signal": "BUY", "price": 100.0})
        self.adapter.execute({"signal": "SELL", "price": 105.0})
        assert len(self.adapter.order_log) == 2

    def test_not_running_raises(self):
        self.adapter.stop()
        with pytest.raises(RuntimeError):
            self.adapter.execute({"signal": "BUY", "price": 100.0})
