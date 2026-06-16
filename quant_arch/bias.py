from __future__ import annotations
from pydantic import BaseModel
from .types import StrategyState

class BiasReport(BaseModel):
    flags: list[str]

def audit_bias(state: StrategyState, recent_returns: list[float]) -> BiasReport:
    flags = []
    if len(recent_returns) >= 20:
        first = recent_returns[:len(recent_returns)//2]
        second = recent_returns[len(recent_returns)//2:]
        first_mean = sum(first)/len(first)
        second_mean = sum(second)/len(second)
        if abs(first_mean - second_mean) > 0.01:
            flags.append('regime_instability')
    if state.sharpe_like < 0:
        flags.append('negative_sharpe')
    return BiasReport(flags=flags)
