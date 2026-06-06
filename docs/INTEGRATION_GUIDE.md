# De-ASI-INTERFACE — Developer Integration Guide

## Quick Start

```bash
# 1. Clone the repository
git clone https://github.com/De-ASI-INTERFACE/De-ASI-INTERFACE.git
cd De-ASI-INTERFACE

# 2. Create virtual environment
python -m venv venv && source venv/bin/activate  # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run all tests
pytest tests/ -v

# 5. Set environment variables
export SOLANA_RPC_URL="https://api.devnet.solana.com"
export JUPITER_API_URL="https://quote-api.jup.ag/v6"
```

## Example: Running a Full Strategy Cycle

```python
from src.agents.signal_agent import SignalAgent
from src.agents.execution_adapter import ExecutionAdapter
from src.strategy.orchestrator import StrategyOrchestrator
from src.strategy.monitor import StrategyMonitor

# Initialize agents
signal_agent = SignalAgent("main-signal", thresholds={"rsi_oversold": 30, "rsi_overbought": 70, "momentum": 0.02})
execution_adapter = ExecutionAdapter("main-exec", venue="paper", slippage_bps=30)

# Start agents
signal_agent.start()
execution_adapter.start()

# Build orchestrator and monitor
orchestrator = StrategyOrchestrator(signal_agent, execution_adapter, max_position_size=500.0)
monitor = StrategyMonitor("main_strategy")

# Run a cycle
market_data = {"price": 145.23, "rsi": 27.5, "momentum": 0.031}
result = orchestrator.run_cycle(market_data)
monitor.record_cycle(result)

print(result)
print(monitor.get_metrics())
```

## Example: Using the ASI Registry

```python
from src.asi.asi_registry import ASIRegistry
from src.asi.interop_bridge import InteropBridge

registry = ASIRegistry()
registry.register("signal-agent-001", ["trading", "signal"], metadata={"version": "1.0"})
registry.register("monitor-agent-001", ["monitoring", "reporting"])

# Find all agents with trading capability
traders = registry.lookup("trading")
print(f"Trading agents: {traders}")

# Pub/sub message routing
bridge = InteropBridge()
bridge.subscribe("trade.signal", lambda msg: print(f"Received: {msg}"))
bridge.publish("trade.signal", {"signal": "BUY", "price": 145.23, "confidence": 0.78})
```

## Example: Solana Connectors

```python
from src.connectors.solana_rpc import SolanaRPCConnector
from src.connectors.jupiter_dex import JupiterDEXConnector
from src.connectors.spl_token import SPLTokenConnector, KNOWN_MINTS

# RPC connector
rpc = SolanaRPCConnector(rpc_url="https://api.mainnet-beta.solana.com")
print(rpc.get_slot())

# Jupiter DEX quote
jup = JupiterDEXConnector(slippage_bps=50)
quote = jup.get_quote(KNOWN_MINTS["SOL"], KNOWN_MINTS["USDC"], 1_000_000_000)
print(f"Jupiter quote: {quote}")

# SPL token
spl = SPLTokenConnector(rpc=rpc)
print(spl.resolve_mint("USDC"))
```

## Prometheus Metrics Endpoint

```python
from src.strategy.monitor import StrategyMonitor

monitor = StrategyMonitor("production")
# ... run cycles ...
print(monitor.prometheus_export())
# Output can be scraped by Prometheus or logged to Grafana Loki
```

## Health Checks

Every module exposes `.health_check() -> bool`. Integrate with your monitoring:

```python
assert signal_agent.health_check()
assert execution_adapter.health_check()
assert orchestrator.health_check()
assert rpc.health_check()
assert jup.health_check()
assert spl.health_check()
assert registry.health_check()
assert bridge.health_check()
assert monitor.health_check()
```
