from __future__ import annotations
from .types import Signal, Hypothesis

def build_hypothesis(signal: Signal) -> Hypothesis:
    expected_return = 0.003 + 0.02 * signal.strength
    volatility = 0.01 + 0.015 * (1 - signal.strength)
    if signal.direction == 'short':
        expected_return *= -1
    return Hypothesis(
        claim=f"{signal.name} implies {signal.direction} edge",
        direction=signal.direction,
        evidence=signal.evidence,
        expected_return=expected_return,
        volatility=volatility,
    )
