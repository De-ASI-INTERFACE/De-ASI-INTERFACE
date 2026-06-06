"""SPL Token Connector.

Provides utilities for reading SPL token metadata, balances,
and mint information from the Solana blockchain.
"""
from typing import Any, Dict, Optional
import logging
from .solana_rpc import SolanaRPCConnector

logger = logging.getLogger(__name__)

# Common SPL mint addresses
KNOWN_MINTS = {
    "USDC": "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v",
    "SOL": "So11111111111111111111111111111111111111112",
    "BONK": "DezXAZ8z7PnrnRJjz3wXBoRgixCa6xjnB7YaB1pPB263",
}


class SPLTokenConnector:
    """Reads SPL token data from Solana via RPC."""

    def __init__(self, rpc: Optional[SolanaRPCConnector] = None):
        self.rpc = rpc or SolanaRPCConnector()

    def get_token_balance(self, token_account: str) -> Dict[str, Any]:
        """Return token balance for an associated token account."""
        result = self.rpc._rpc_call("getTokenAccountBalance", [token_account])
        logger.debug(f"Token balance for {token_account}: {result}")
        return result

    def get_mint_info(self, mint_address: str) -> Dict[str, Any]:
        """Return mint account info (supply, decimals, authority)."""
        result = self.rpc._rpc_call("getAccountInfo", [mint_address, {"encoding": "jsonParsed"}])
        logger.debug(f"Mint info for {mint_address}: {result}")
        return result

    def resolve_mint(self, symbol: str) -> Optional[str]:
        """Resolve a known token symbol to its mint address."""
        return KNOWN_MINTS.get(symbol.upper())

    def health_check(self) -> bool:
        return self.rpc.health_check()
