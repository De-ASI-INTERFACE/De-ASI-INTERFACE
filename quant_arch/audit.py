from __future__ import annotations
import json
from pathlib import Path

class AuditLog:
    def __init__(self, path: str):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def append(self, record: dict):
        with self.path.open('a', encoding='utf-8') as f:
            f.write(json.dumps(record, default=str) + '\n')
