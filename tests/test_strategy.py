"""Tests — Strategy Orchestration & Real-Time Monitoring
Owner/Creator: Richard Patterson | © 2026 Richard Patterson
"""
import sys, pathlib, time
sys.path.insert(0, str(pathlib.Path(__file__).parents[1]))

import pytest
from src.agents.signal_agent import SignalAgent
from src.agents.execution_adapter import ExecutionAdapter
from src.strategy.orchestrator import StrategyOrchestrator
from src.strategy.monitor import StrategyMonitor


def _orch(venue="paper"):
    s = SignalAgent("os"); s.start()
    e = ExecutionAdapter("oe", venue=venue); e.start()
    return StrategyOrchestrator(s, e, max_position_size=100.0)


class TestStrategyOrchestrator:
    def setup_method(self): self.o = _orch()
    def test_health(self):          assert self.o.health_check()
    def test_hold_blocked(self):    r=self.o.run_cycle({"price":100.0,"rsi":50.0,"momentum":0.0}); assert r["status"]=="blocked"
    def test_buy_filled(self):      r=self.o.run_cycle({"price":50.0,"rsi":25.0,"momentum":0.05}); assert r.get("signal")=="BUY" and r.get("status")=="filled"
    def test_sell_filled(self):     r=self.o.run_cycle({"price":200.0,"rsi":75.0,"momentum":-0.05}); assert r.get("signal")=="SELL" and r.get("status")=="filled"
    def test_log_grows(self):       self.o.run_cycle({"price":50.0,"rsi":25.0,"momentum":0.05}); self.o.run_cycle({"price":50.0,"rsi":25.0,"momentum":0.05}); assert len(self.o.trade_log)==2
    def test_size_positive(self):   r=self.o.run_cycle({"price":50.0,"rsi":25.0,"momentum":0.05}); assert r.get("size",0)>0
    def test_summary(self):         self.o.run_cycle({"price":50.0,"rsi":25.0,"momentum":0.05}); s=self.o.get_summary(); assert s["total_cycles"]==1 and "pnl" in s
    def test_summary_empty(self):   assert self.o.get_summary()["last_trade"] is None
    def test_low_conf_blocked(self):
        s=SignalAgent("lc"); s.start(); e=ExecutionAdapter("lce"); e.start()
        o=StrategyOrchestrator(s,e); r=o.run_cycle({"price":100.0,"rsi":50.0,"momentum":0.0})
        assert r["status"]=="blocked"
    def test_size_capped(self):
        s=SignalAgent("cap"); s.start(); e=ExecutionAdapter("cape"); e.start()
        o=StrategyOrchestrator(s,e,max_position_size=10.0)
        r=o.run_cycle({"price":50.0,"rsi":1.0,"momentum":100.0})
        if r.get("status")=="filled": assert r["size"]<=10.0


class TestStrategyMonitor:
    def setup_method(self): self.m = StrategyMonitor("test")
    def test_health(self):          assert self.m.health_check()
    def test_initial_zeros(self):   mx=self.m.get_metrics(); assert mx["cycles"]==0 and mx["signals_buy"]==0
    def test_buy_recorded(self):    self.m.record_cycle({"signal":"BUY","status":"filled"}); mx=self.m.get_metrics(); assert mx["signals_buy"]==1 and mx["orders_filled"]==1
    def test_sell_recorded(self):   self.m.record_cycle({"signal":"SELL","status":"filled"}); assert self.m.get_metrics()["signals_sell"]==1
    def test_blocked_recorded(self):self.m.record_cycle({"signal":"HOLD","status":"blocked"}); mx=self.m.get_metrics(); assert mx["risk_blocked"]==1 and mx["signals_hold"]==1
    def test_skipped_recorded(self):self.m.record_cycle({"signal":"HOLD","status":"skipped"}); assert self.m.get_metrics()["orders_skipped"]==1
    def test_prometheus_format(self):self.m.record_cycle({"signal":"BUY","status":"filled"}); out=self.m.prometheus_export(); assert "deasi_test_cycles" in out and "# TYPE" in out
    def test_reset(self):           self.m.record_cycle({"signal":"BUY","status":"filled"}); self.m.reset(); assert self.m.get_metrics()["cycles"]==0
    def test_uptime_positive(self): time.sleep(0.01); assert self.m.get_metrics()["uptime_seconds"]>0
    def test_multi_cycles(self):    [self.m.record_cycle({"signal":"BUY","status":"filled"}) for _ in range(10)]; assert self.m.get_metrics()["cycles"]==10
    def test_count_increments(self):self.m.record_cycle({"signal":"SELL","status":"filled"}); self.m.record_cycle({"signal":"BUY","status":"filled"}); assert self.m.get_metrics()["cycles"]==2
