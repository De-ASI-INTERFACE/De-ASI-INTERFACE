from __future__ import annotations
from pydantic import BaseModel, Field
from typing import Literal
from datetime import datetime

class MarketRow(BaseModel):
    ts: datetime
    price: float
    volume: float
    imbalance: float
    funding: float
    macro: float

class Signal(BaseModel):
    name: str
    direction: Literal['long','short']
    strength: float
    evidence: dict

class Hypothesis(BaseModel):
    claim: str
    direction: Literal['long','short']
    evidence: dict
    expected_return: float
    volatility: float

class Distribution(BaseModel):
    mean: float
    std: float
    p05: float
    p95: float
    confidence: float

class ExecutionDecision(BaseModel):
    direction: Literal['long','short','flat']
    size: float
    override: bool = False
    reason: str = ''

class StrategyState(BaseModel):
    equity: float = 1.0
    peak_equity: float = 1.0
    returns_count: int = 0
    mean_return: float = 0.0
    m2: float = 0.0
    active: bool = True

    def update_return(self, r: float):
        self.returns_count += 1
        delta = r - self.mean_return
        self.mean_return += delta / self.returns_count
        delta2 = r - self.mean_return
        self.m2 += delta * delta2
        self.equity *= (1 + r)
        self.peak_equity = max(self.peak_equity, self.equity)

    @property
    def variance(self) -> float:
        return self.m2 / (self.returns_count - 1) if self.returns_count > 1 else 0.0

    @property
    def sharpe_like(self) -> float:
        import math
        v = self.variance
        return self.mean_return / math.sqrt(v) if v > 1e-12 else 0.0

    @property
    def drawdown(self) -> float:
        return 1 - (self.equity / self.peak_equity if self.peak_equity else 1.0)
