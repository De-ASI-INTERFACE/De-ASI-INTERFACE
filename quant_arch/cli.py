from __future__ import annotations
import argparse
from .engine import run_pipeline

def main():
    p = argparse.ArgumentParser()
    p.add_argument('--input', required=True)
    p.add_argument('--audit', required=True)
    p.add_argument('--output', required=True)
    args = p.parse_args()
    df = run_pipeline(args.input, args.audit)
    df.to_csv(args.output, index=False)

if __name__ == '__main__':
    main()
