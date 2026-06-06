"""Tests — AI Agent Execution Adapters
Owner/Creator: Richard Patterson | © 2026 Richard Patterson
"""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).parents[1]))

import pytest
from src.agents.signal_agent import SignalAgent
from src.agents.execution_adapter import ExecutionAdapter


@pytest.fixture
def sig():
    a = SignalAgent("t-sig-001")
    a.start()
    return a

@pytest.fixture
def exe():
    a = ExecutionAdapter("t-exe-001", venue="paper")
    a.start()
    return a


class TestSignalAgent:
    def test_init(self, sig):
        assert sig.agent_id == "t-sig-001" and sig.is_running

    def test_health_running(self, sig):
        assert sig.health_check()

    def test_health_stopped(self, sig):
        sig.stop()
        assert not sig.health_check()

    def test_hold_neutral(self, sig):
        r = sig.execute({"price": 100.0, "rsi": 50.0, "momentum": 0.0})
        assert r["signal"] == "HOLD"

    def test_buy_oversold(self, sig):
        r = sig.execute({"price": 50.0, "rsi": 25.0, "momentum": 0.05})
        assert r["signal"] == "BUY" and r["confidence"] > 0.5

    def test_sell_overbought(self, sig):
        r = sig.execute({"price": 200.0, "rsi": 75.0, "momentum": -0.05})
        assert r["signal"] == "SELL" and r["confidence"] > 0.5

    def test_missing_price_raises(self, sig):
        with pytest.raises(ValueError):
            sig.execute({"rsi": 50.0})

    def test_not_running_raises(self, sig):
        sig.stop()
        with pytest.raises(RuntimeError):
            sig.execute({"price": 100.0})

    def test_history_accumulates(self, sig):
        sig.execute({"price": 100.0, "rsi": 50.0})
        sig.execute({"price": 101.0, "rsi": 50.0})
        assert len(sig.signal_history) == 2

    def test_last_signal(self, sig):
        sig.execute({"price": 100.0, "rsi": 50.0})
        assert sig.get_last_signal() is not None

    def test_last_signal_empty(self):
        a = SignalAgent("empty")
        a.start()
        assert a.get_last_signal() is None

    def test_confidence_capped(self, sig):
        r = sig.execute({"price": 50.0, "rsi": 1.0, "momentum": 100.0})
        assert r["confidence"] <= 0.99

    def test_rsi_boundary_buy(self, sig):
        r = sig.execute({"price": 50.0, "rsi": 29.9, "momentum": 0.001})
        assert r["signal"] == "BUY"

    def test_rsi_boundary_sell(self, sig):
        r = sig.execute({"price": 50.0, "rsi": 70.1, "momentum": -0.001})
        assert r["signal"] == "SELL"

    def test_zero_price_allowed(self, sig):
        r = sig.execute({"price": 0.0, "rsi": 50.0})
        assert r["price"] == 0.0

    def test_negative_momentum_hold(self, sig):
        r = sig.execute({"price": 50.0, "rsi": 25.0, "momentum": -0.05})
        assert r["signal"] == "HOLD"

    def test_repr(self, sig):
        assert "t-sig-001" in repr(sig)


class TestExecutionAdapter:
    def test_init(self, exe):
        assert exe.venue == "paper" and exe.slippage_bps == 30

    def test_invalid_venue(self):
        with pytest.raises(ValueError):
            ExecutionAdapter("bad", venue="invalid")

    def test_health(self, exe):
        assert exe.health_check()

    def test_buy_filled(self, exe):
        r = exe.execute({"signal": "BUY", "price": 100.0})
        assert r["status"] == "filled" and r["effective_price"] > 100.0

    def test_sell_filled(self, exe):
        r = exe.execute({"signal": "SELL", "price": 100.0})
        assert r["status"] == "filled" and r["effective_price"] < 100.0

    def test_hold_skipped(self, exe):
        r = exe.execute({"signal": "HOLD", "price": 100.0})
        assert r["status"] == "skipped"

    def test_order_log_grows(self, exe):
        exe.execute({"signal": "BUY",  "price": 100.0})
        exe.execute({"signal": "SELL", "price": 105.0})
        assert len(exe.order_log) == 2

    def test_not_running_raises(self, exe):
        exe.stop()
        with pytest.raises(RuntimeError):
            exe.execute({"signal": "BUY", "price": 100.0})

    def test_slippage_zero(self):
        a = ExecutionAdapter("zero-slip", venue="paper", slippage_bps=0)
        a.start()
        r = a.execute({"signal": "BUY", "price": 100.0})
        assert r["effective_price"] == 100.0

    def test_size_passed_through(self, exe):
        r = exe.execute({"signal": "BUY", "price": 100.0, "size": 7.5})
        assert r["size"] == 7.5

    def test_solana_dex_venue_pending(self):
        a = ExecutionAdapter("dex", venue="solana_dex")
        a.start()
        r = a.execute({"signal": "BUY", "price": 100.0})
        assert r["status"] == "pending"

    def test_health_stopped(self, exe):
        exe.stop()
        assert not exe.health_check()
