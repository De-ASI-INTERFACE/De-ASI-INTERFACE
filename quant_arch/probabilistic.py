from __future__ import annotations
import numpy as np
from .types import Hypothesis, Distribution

def monte_carlo_distribution(h: Hypothesis, paths: int, alpha: float) -> Distribution:
    rng = np.random.default_rng(42)
    sims = rng.normal(loc=h.expected_return, scale=h.volatility, size=paths)
    mean = float(np.mean(sims))
    std = float(np.std(sims))
    p05, p95 = np.quantile(sims, [alpha, 1-alpha])
    conf = float(np.mean(sims > 0)) if h.direction == 'long' else float(np.mean(sims < 0))
    return Distribution(mean=mean, std=std, p05=float(p05), p95=float(p95), confidence=conf)
