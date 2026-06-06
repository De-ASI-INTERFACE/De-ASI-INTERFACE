"""Jupiter DEX Connector (v6 aggregator).
Owner/Creator: Richard Patterson
© 2026 Richard Patterson. All Rights Reserved.
"""
from typing import Any, Dict, Optional
import os, logging

logger = logging.getLogger(__name__)
JUPITER_API_BASE = os.getenv("JUPITER_API_URL", "https://quote-api.jup.ag/v6")


class JupiterDEXConnector:
    def __init__(self, api_base: Optional[str] = None, slippage_bps: int = 50):
        self.api_base      = api_base or JUPITER_API_BASE
        self.slippage_bps  = slippage_bps

    def get_quote(self, input_mint: str, output_mint: str,
                  amount_lamports: int) -> Dict[str, Any]:
        return {
            "inputMint": input_mint, "outputMint": output_mint,
            "amount": amount_lamports,
            "outAmount": int(amount_lamports * 0.998),
            "priceImpactPct": "0.02",
            "slippageBps": self.slippage_bps, "_stub": True,
        }

    def build_swap_transaction(self, quote: Dict[str, Any],
                               user_pubkey: str) -> Dict[str, Any]:
        return {"swapTransaction": "BASE64_TX_STUB",
                "userPubkey": user_pubkey, "quote": quote, "_stub": True}

    def health_check(self) -> bool:
        q = self.get_quote(
            "So11111111111111111111111111111111111111112",
            "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v",
            1_000_000)
        return "outAmount" in q
