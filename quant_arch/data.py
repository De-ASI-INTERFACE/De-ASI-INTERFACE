from __future__ import annotations
import pandas as pd
from .types import MarketRow

class DomainContext:
    def __init__(self, csv_path: str):
        self.df = pd.read_csv(csv_path, parse_dates=['ts'])
        required = {'ts','price','volume','imbalance','funding','macro'}
        missing = required - set(self.df.columns)
        if missing:
            raise ValueError(f'Missing columns: {missing}')

    def snapshot(self, idx: int) -> MarketRow:
        row = self.df.iloc[idx].to_dict()
        return MarketRow(**row)
