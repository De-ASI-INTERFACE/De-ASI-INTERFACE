from __future__ import annotations
import pandas as pd
from .types import Signal

def generate_signals(df: pd.DataFrame, idx: int, lookback: int) -> list[Signal]:
    if idx < max(lookback, 20):
        return []
    window = df.iloc[idx-lookback:idx]
    px = window['price']
    ma_fast = px.tail(10).mean()
    ma_slow = px.mean()
    vol_z = (window['volume'].iloc[-1] - window['volume'].mean()) / (window['volume'].std() + 1e-9)
    imb = window['imbalance'].iloc[-1]
    funding = window['funding'].iloc[-1]
    signals = []
    trend_strength = (ma_fast - ma_slow) / (ma_slow + 1e-9)
    if abs(trend_strength) > 0.001:
        direction = 'long' if trend_strength > 0 else 'short'
        signals.append(Signal(name='trend', direction=direction, strength=min(abs(trend_strength)*50,1.0), evidence={'trend_strength': float(trend_strength)}))
    micro_strength = 0.5 * imb + 0.1 * vol_z - 0.2 * funding
    if abs(micro_strength) > 0.1:
        direction = 'long' if micro_strength > 0 else 'short'
        signals.append(Signal(name='microstructure', direction=direction, strength=min(abs(micro_strength),1.0), evidence={'imbalance': float(imb), 'volume_z': float(vol_z), 'funding': float(funding)}))
    return signals

def score_signal(signal: Signal) -> float:
    payoff = 0.02 + 0.03 * signal.strength
    prob = 0.5 + 0.25 * signal.strength
    return prob * payoff - (1-prob)*0.01
