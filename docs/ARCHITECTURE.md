# De-ASI-INTERFACE — System Architecture

## Overview

De-ASI-INTERFACE is a modular, Solana-native agentic finance infrastructure layer. It is organized into four execution domains, each with clean interfaces, full test coverage, and Prometheus-compatible observability.

```
De-ASI-INTERFACE/
├── src/
│   ├── agents/          # AI Agent Execution Adapters
│   ├── connectors/      # Solana Trading & DeFi Connectors
│   ├── asi/             # ASI Ecosystem Integration Modules
│   └── strategy/        # Orchestration & Real-Time Monitoring
├── tests/               # 100% coverage unit test suite
├── docs/                # Developer documentation
└── .github/workflows/   # CI/CD pipeline (pytest + lint)
```

## Module Descriptions

### `src/agents/`
- **`base_agent.py`** — Abstract interface all agents implement (`execute`, `health_check`, `start`, `stop`)
- **`signal_agent.py`** — RSI + momentum signal generator emitting BUY/SELL/HOLD with confidence scores
- **`execution_adapter.py`** — Routes validated signals to `paper`, `solana_dex`, or `cex_maker` venues with slippage modeling

### `src/connectors/`
- **`solana_rpc.py`** — JSON-RPC 2.0 interface: balance, slot, transaction fetch, send
- **`jupiter_dex.py`** — Jupiter Aggregator v6 quote and swap transaction builder
- **`spl_token.py`** — SPL token balance, mint info, and symbol-to-mint resolution

### `src/asi/`
- **`asi_registry.py`** — Agent registration, capability lookup, and lifecycle management
- **`interop_bridge.py`** — Pub/sub message router for cross-agent and cross-ecosystem communication

### `src/strategy/`
- **`orchestrator.py`** — Full trade lifecycle: signal → risk check → Kelly sizing → execution → P&L logging
- **`monitor.py`** — Real-time cycle metrics with Prometheus text export and Grafana-ready structured logging

## Data Flow

```
Market Data Feed
      ↓
  SignalAgent  →  confidence score
      ↓
  StrategyOrchestrator  →  risk check →  position sizing
      ↓
  ExecutionAdapter  →  venue routing (Solana DEX / CEX / Paper)
      ↓
  StrategyMonitor  →  Prometheus metrics →  Grafana dashboard
      ↓
  InteropBridge  →  ASI ecosystem pub/sub
```

## Risk Controls

- Minimum confidence threshold (0.55) before any order is sent
- Kelly-inspired fractional position sizing capped at `max_position_size`
- Slippage modeled at execution time (BPS-configurable)
- All HOLD signals are blocked at the orchestrator level — never reach execution

## Environment Variables

| Variable | Default | Description |
|---|---|---|
| `SOLANA_RPC_URL` | mainnet-beta | Solana JSON-RPC endpoint |
| `JUPITER_API_URL` | jup.ag v6 | Jupiter swap API base URL |

All secrets (wallet keys, API tokens) must be passed via environment variables — never committed to source.
