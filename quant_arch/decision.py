from __future__ import annotations
from .types import Distribution, ExecutionDecision, StrategyState
from .config import AppConfig

def decide(dist: Distribution, state: StrategyState, cfg: AppConfig, direction: str) -> ExecutionDecision:
    if not state.active:
        return ExecutionDecision(direction='flat', size=0.0, override=True, reason='strategy_inactive')
    if state.drawdown > cfg.risk.max_drawdown:
        return ExecutionDecision(direction='flat', size=0.0, override=True, reason='drawdown_breach')
    edge = abs(dist.mean) / (dist.std + 1e-9)
    size = min(cfg.risk.max_position, max(0.0, edge * dist.confidence))
    if dist.confidence < 0.52 or size == 0.0:
        return ExecutionDecision(direction='flat', size=0.0, reason='insufficient_confidence')
    return ExecutionDecision(direction=direction, size=float(size), reason='autonomous_execution')
