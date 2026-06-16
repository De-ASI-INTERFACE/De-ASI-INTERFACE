from __future__ import annotations
from .types import Signal, Hypothesis, Distribution, ExecutionDecision

def build_report(signal: Signal, hypothesis: Hypothesis, dist: Distribution, decision: ExecutionDecision) -> dict:
    return {
        'signal': signal.model_dump(),
        'hypothesis': hypothesis.model_dump(),
        'distribution': dist.model_dump(),
        'decision': decision.model_dump(),
    }
