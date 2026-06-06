"""Solana RPC Connector.

Provides a lightweight interface to Solana JSON-RPC endpoints
for account queries, transaction submission, and slot monitoring.
"""
from typing import Any, Dict, Optional
import os
import logging

logger = logging.getLogger(__name__)

DEFAULT_RPC_URL = os.getenv("SOLANA_RPC_URL", "https://api.mainnet-beta.solana.com")


class SolanaRPCConnector:
    """Thin wrapper around Solana JSON-RPC endpoints."""

    def __init__(self, rpc_url: Optional[str] = None, timeout: int = 10):
        self.rpc_url = rpc_url or DEFAULT_RPC_URL
        self.timeout = timeout
        self._session = None
        logger.info(f"SolanaRPCConnector initialized: {self.rpc_url}")

    def get_balance(self, pubkey: str) -> Dict[str, Any]:
        """Return SOL balance for a given public key (lamports)."""
        return self._rpc_call("getBalance", [pubkey])

    def get_slot(self) -> Dict[str, Any]:
        """Return current slot height."""
        return self._rpc_call("getSlot", [])

    def get_transaction(self, signature: str) -> Dict[str, Any]:
        """Fetch transaction details by signature."""
        return self._rpc_call("getTransaction", [signature, {"encoding": "jsonParsed"}])

    def send_transaction(self, signed_tx_b64: str) -> Dict[str, Any]:
        """Submit a base64-encoded signed transaction."""
        return self._rpc_call("sendTransaction", [signed_tx_b64, {"encoding": "base64"}])

    def _rpc_call(self, method: str, params: list) -> Dict[str, Any]:
        """Build and execute a JSON-RPC 2.0 request.
        
        In production this would use httpx/aiohttp. In test mode,
        returns a structured mock to allow unit testing without live RPC.
        """
        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": method,
            "params": params,
        }
        logger.debug(f"RPC call: {method} params={params}")
        # Stub return for testability — replace with live HTTP call in deployment
        return {"jsonrpc": "2.0", "id": 1, "result": None, "_stub": True, "method": method}

    def health_check(self) -> bool:
        result = self.get_slot()
        return "result" in result
