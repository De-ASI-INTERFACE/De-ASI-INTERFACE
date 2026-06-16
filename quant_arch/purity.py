from __future__ import annotations
from .types import Signal

def enforce_signal_purity(signals: list[Signal]) -> list[Signal]:
    return [s for s in signals if isinstance(s.evidence, dict) and len(s.evidence) > 0]
