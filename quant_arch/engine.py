from __future__ import annotations
import pandas as pd
from .config import AppConfig
from .data import DomainContext
from .signals import generate_signals, score_signal
from .hypothesis import build_hypothesis
from .probabilistic import monte_carlo_distribution
from .decision import decide
from .bias import audit_bias
from .purity import enforce_signal_purity
from .reporting import build_report
from .audit import AuditLog
from .types import StrategyState

def run_pipeline(csv_path: str, audit_path: str, cfg: AppConfig | None = None) -> pd.DataFrame:
    cfg = cfg or AppConfig()
    ctx = DomainContext(csv_path)
    df = ctx.df.copy()
    state = StrategyState()
    audit = AuditLog(audit_path)
    realized = []
    rows = []
    for idx in range(len(df)-1):
        raw = generate_signals(df, idx, cfg.model.lookback)
        pure = enforce_signal_purity(raw)
        if not pure:
            continue
        best = max(pure, key=score_signal)
        if score_signal(best) < cfg.risk.min_signal_ev:
            continue
        hyp = build_hypothesis(best)
        dist = monte_carlo_distribution(hyp, cfg.model.monte_carlo_paths, cfg.model.confidence_alpha)
        decision = decide(dist, state, cfg, best.direction)
        next_ret = (df.iloc[idx+1]['price'] / df.iloc[idx]['price']) - 1
        signed_ret = next_ret if decision.direction == 'long' else (-next_ret if decision.direction == 'short' else 0.0)
        pnl = decision.size * signed_ret
        state.update_return(pnl)
        realized.append(pnl)
        if len(realized) > 40:
            realized = realized[-40:]
        bias = audit_bias(state, realized)
        if 'negative_sharpe' in bias.flags and state.returns_count > 30:
            state.active = False
        report = build_report(best, hyp, dist, decision)
        report['bias_flags'] = bias.flags
        report['pnl'] = pnl
        report['equity'] = state.equity
        audit.append(report)
        rows.append({
            'ts': df.iloc[idx]['ts'],
            'signal': best.name,
            'direction': decision.direction,
            'size': decision.size,
            'confidence': dist.confidence,
            'pnl': pnl,
            'equity': state.equity,
            'drawdown': state.drawdown,
            'active': state.active,
            'bias_flags': ','.join(bias.flags),
        })
    return pd.DataFrame(rows)
