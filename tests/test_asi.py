"""Unit tests for ASI Ecosystem Integration Modules."""
import pytest
from src.asi.asi_registry import ASIRegistry
from src.asi.interop_bridge import InteropBridge


class TestASIRegistry:
    def setup_method(self):
        self.registry = ASIRegistry()

    def test_health_check(self):
        assert self.registry.health_check() is True

    def test_register_agent(self):
        result = self.registry.register("agent-001", ["trading", "signal"])
        assert result is True
        assert self.registry.count() == 1

    def test_lookup_by_capability(self):
        self.registry.register("agent-001", ["trading", "signal"])
        self.registry.register("agent-002", ["monitoring"])
        traders = self.registry.lookup("trading")
        assert "agent-001" in traders
        assert "agent-002" not in traders

    def test_deregister_agent(self):
        self.registry.register("agent-001", ["trading"])
        result = self.registry.deregister("agent-001")
        assert result is True
        assert self.registry.count() == 0

    def test_deregister_nonexistent_returns_false(self):
        assert self.registry.deregister("nonexistent") is False

    def test_get_agent_returns_correct_data(self):
        self.registry.register("agent-001", ["trading"], metadata={"version": "1.0"})
        data = self.registry.get_agent("agent-001")
        assert data["capabilities"] == ["trading"]
        assert data["metadata"]["version"] == "1.0"

    def test_list_all(self):
        self.registry.register("agent-001", ["trading"])
        self.registry.register("agent-002", ["monitoring"])
        all_agents = self.registry.list_all()
        assert len(all_agents) == 2

    def test_overwrite_existing_agent(self):
        self.registry.register("agent-001", ["trading"])
        self.registry.register("agent-001", ["monitoring"])  # overwrite
        data = self.registry.get_agent("agent-001")
        assert data["capabilities"] == ["monitoring"]


class TestInteropBridge:
    def setup_method(self):
        self.bridge = InteropBridge()

    def test_health_check(self):
        assert self.bridge.health_check() is True

    def test_publish_no_subscribers_returns_zero(self):
        count = self.bridge.publish("trade.signal", {"signal": "BUY"})
        assert count == 0

    def test_subscribe_and_receive(self):
        received = []
        self.bridge.subscribe("trade.signal", lambda msg: received.append(msg))
        self.bridge.publish("trade.signal", {"signal": "BUY", "price": 100.0})
        assert len(received) == 1
        assert received[0]["signal"] == "BUY"

    def test_multiple_subscribers(self):
        received_a, received_b = [], []
        self.bridge.subscribe("topic", lambda m: received_a.append(m))
        self.bridge.subscribe("topic", lambda m: received_b.append(m))
        count = self.bridge.publish("topic", {"data": 1})
        assert count == 2
        assert len(received_a) == 1
        assert len(received_b) == 1

    def test_message_log_recorded(self):
        self.bridge.publish("topic", {"x": 1})
        log = self.bridge.get_log()
        assert len(log) == 1
        assert log[0]["topic"] == "topic"

    def test_clear_log(self):
        self.bridge.publish("topic", {"x": 1})
        self.bridge.clear_log()
        assert len(self.bridge.get_log()) == 0

    def test_handler_exception_does_not_crash_bridge(self):
        def bad_handler(msg):
            raise RuntimeError("handler failure")
        self.bridge.subscribe("topic", bad_handler)
        count = self.bridge.publish("topic", {"x": 1})  # must not raise
        assert count == 1
