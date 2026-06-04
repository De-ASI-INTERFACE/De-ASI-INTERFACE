"""De-ASI-INTERFACE ecosystem health checker.
Iteratively pings all public endpoints and Solana RPC.
No recursion. Memory-safe.
Creator: Richard Patterson (@De-ASI-INTERFACE)
"""
from __future__ import annotations

import os
import time
from collections import deque
from typing import Deque
import requests
from dotenv import load_dotenv
from loguru import logger

load_dotenv()

ENDPOINTS: list[dict] = [
    {"name": "Solana Mainnet RPC", "url": os.getenv("SOLANA_RPC_URL", "https://api.mainnet-beta.solana.com"), "method": "post"},
    {"name": "Jupiter API", "url": "https://price.jup.ag/v4/price?ids=SOL", "method": "get"},
    {"name": "LWC API (local)", "url": "http://localhost:8000/health", "method": "get"},
]


def check_endpoint(endpoint: dict, timeout: int = 8) -> dict:
    result: dict = {"name": endpoint["name"], "url": endpoint["url"], "ts": time.time()}
    try:
        if endpoint["method"] == "post":
            resp = requests.post(
                endpoint["url"],
                json={"jsonrpc": "2.0", "id": 1, "method": "getHealth"},
                timeout=timeout,
            )
        else:
            resp = requests.get(endpoint["url"], timeout=timeout)
        result["status"] = resp.status_code
        result["ok"] = resp.status_code < 400
        result["latency_ms"] = int((time.time() - result["ts"]) * 1000)
    except Exception as exc:
        result["status"] = 0
        result["ok"] = False
        result["error"] = str(exc)
    return result


def run_health_checks() -> list[dict]:
    """Run all endpoint checks iteratively."""
    results: list[dict] = []
    for endpoint in ENDPOINTS:
        result = check_endpoint(endpoint)
        results.append(result)
        status = "✅" if result["ok"] else "❌"
        logger.info(f"{status} {result['name']}: {result.get('status', 'ERR')} ({result.get('latency_ms', '?')}ms)")
    return results


if __name__ == "__main__":
    run_health_checks()
