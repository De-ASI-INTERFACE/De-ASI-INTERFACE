# Modular Quantitative Architecture

Tradecraft-informed 10-layer quantitative pipeline built on Jack Davis's DI analyst axioms.

## Layers

| Layer | Module | Axiom Source |
|---|---|---|
| 1 | `data.py` | Domain Mastery |
| 2 | `signals.py` | Relevance & Prioritization |
| 3 | `hypothesis.py` | Intellectual Rigor |
| 4 | `decision.py` | Analytical Independence |
| 5 | `probabilistic.py` | Probabilistic Thinking |
| 6 | `engine.py` feedback loop | Error Tolerance & Adaptation |
| 7 | `bias.py` | Bias Recognition & Mitigation |
| 8 | `purity.py` | Objectivity & Non-Advocacy |
| 9 | `reporting.py` | Communication Clarity |
| 10 | `audit.py` | Accountability & Ownership |

## Install

```bash
pip install -e .
```

## Run

```bash
quant-arch --input example_market_data.csv --audit audit.jsonl --output results.csv
```

## Python API

```python
from quant_arch.engine import run_pipeline
df = run_pipeline('example_market_data.csv', 'audit.jsonl')
print(df)
```
