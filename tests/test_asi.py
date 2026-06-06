"""Tests — ASI Ecosystem Integration Modules
Owner/Creator: Richard Patterson | © 2026 Richard Patterson
"""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).parents[1]))

import pytest
from src.asi.asi_registry import ASIRegistry
from src.asi.interop_bridge import InteropBridge


class TestASIRegistry:
    def setup_method(self):
        self.reg = ASIRegistry()

    def test_health(self):             assert self.reg.health_check()
    def test_register(self):           assert self.reg.register("a1", ["trading"]) and self.reg.count() == 1
    def test_lookup_match(self):       self.reg.register("a1",["trading","signal"]); self.reg.register("a2",["monitoring"]); assert "a1" in self.reg.lookup("trading") and "a2" not in self.reg.lookup("trading")
    def test_lookup_no_match(self):    self.reg.register("a1",["trading"]); assert self.reg.lookup("x") == []
    def test_deregister(self):         self.reg.register("a1",["t"]); assert self.reg.deregister("a1") and self.reg.count()==0
    def test_deregister_missing(self): assert not self.reg.deregister("ghost")
    def test_get_agent(self):          self.reg.register("a1",["t"],metadata={"v":"1.0"}); assert self.reg.get_agent("a1")["metadata"]["v"]=="1.0"
    def test_get_agent_missing(self):  assert self.reg.get_agent("x") is None
    def test_list_all(self):           self.reg.register("a1",["t"]); self.reg.register("a2",["m"]); assert len(self.reg.list_all())==2
    def test_overwrite(self):          self.reg.register("a1",["t"]); self.reg.register("a1",["m"]); assert self.reg.get_agent("a1")["capabilities"]==["m"]
    def test_count(self):              [self.reg.register(f"a{i}",["x"]) for i in range(5)]; assert self.reg.count()==5


class TestInteropBridge:
    def setup_method(self):
        self.br = InteropBridge()

    def test_health(self):                   assert self.br.health_check()
    def test_no_subs(self):                  assert self.br.publish("t",{}) == 0
    def test_subscribe_receive(self):        rcv=[]; self.br.subscribe("t",lambda m:rcv.append(m)); self.br.publish("t",{"v":1}); assert rcv[0]["v"]==1
    def test_multi_subs(self):               a,b=[],[]; self.br.subscribe("t",lambda m:a.append(m)); self.br.subscribe("t",lambda m:b.append(m)); assert self.br.publish("t",{})==2
    def test_log_recorded(self):             self.br.publish("t",{}); assert len(self.br.get_log())==1
    def test_log_topic(self):                self.br.publish("my_topic",{}); assert self.br.get_log()[0]["topic"]=="my_topic"
    def test_clear_log(self):                self.br.publish("t",{}); self.br.clear_log(); assert self.br.get_log()==[]
    def test_handler_exception_no_crash(self): self.br.subscribe("t",lambda m:1/0); assert self.br.publish("t",{})==1
    def test_separate_topics(self):          a=[]; self.br.subscribe("t1",lambda m:a.append(m)); self.br.publish("t2",{}); assert len(a)==0
    def test_delivered_to_in_log(self):      self.br.subscribe("t",lambda m:None); self.br.publish("t",{}); assert self.br.get_log()[0]["delivered_to"]==1
