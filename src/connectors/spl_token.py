"""SPL Token Connector.
Owner/Creator: Richard Patterson
© 2026 Richard Patterson. All Rights Reserved.
"""
from typing import Any, Dict, Optional
import logging
from .solana_rpc import SolanaRPCConnector

logger = logging.getLogger(__name__)

KNOWN_MINTS: Dict[str, str] = {
    "USDC": "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v",
    "SOL":  "So11111111111111111111111111111111111111112",
    "BONK": "DezXAZ8z7PnrnRJjz3wXBoRgixCa6xjnB7YaB1pPB263",
}


class SPLTokenConnector:
    def __init__(self, rpc: Optional[SolanaRPCConnector] = None):
        self.rpc = rpc or SolanaRPCConnector()

    def get_token_balance(self, token_account: str) -> Dict[str, Any]:
        return self.rpc._rpc_call("getTokenAccountBalance", [token_account])

    def get_mint_info(self, mint_address: str) -> Dict[str, Any]:
        return self.rpc._rpc_call(
            "getAccountInfo", [mint_address, {"encoding": "jsonParsed"}])

    def resolve_mint(self, symbol: str) -> Optional[str]:
        return KNOWN_MINTS.get(symbol.upper())

    def health_check(self) -> bool:
        return self.rpc.health_check()
