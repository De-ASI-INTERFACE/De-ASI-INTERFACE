"""Solana RPC Connector.
Owner/Creator: Richard Patterson
© 2026 Richard Patterson. All Rights Reserved.
"""
from typing import Any, Dict, Optional
import os, logging

logger = logging.getLogger(__name__)
DEFAULT_RPC_URL = os.getenv(
    "SOLANA_RPC_URL", "https://api.mainnet-beta.solana.com")


class SolanaRPCConnector:
    """Thin wrapper around Solana JSON-RPC 2.0."""

    def __init__(self, rpc_url: Optional[str] = None, timeout: int = 10):
        self.rpc_url = rpc_url or DEFAULT_RPC_URL
        self.timeout = timeout

    def get_balance(self, pubkey: str) -> Dict[str, Any]:
        return self._rpc_call("getBalance", [pubkey])

    def get_slot(self) -> Dict[str, Any]:
        return self._rpc_call("getSlot", [])

    def get_transaction(self, sig: str) -> Dict[str, Any]:
        return self._rpc_call("getTransaction",
                              [sig, {"encoding": "jsonParsed"}])

    def send_transaction(self, signed_tx_b64: str) -> Dict[str, Any]:
        return self._rpc_call("sendTransaction",
                              [signed_tx_b64, {"encoding": "base64"}])

    def _rpc_call(self, method: str, params: list) -> Dict[str, Any]:
        return {"jsonrpc": "2.0", "id": 1, "result": None,
                "_stub": True, "method": method}

    def health_check(self) -> bool:
        return "result" in self.get_slot()
