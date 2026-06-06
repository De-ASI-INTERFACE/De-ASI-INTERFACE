"""Unit tests for Solana Trading and DeFi Connectors."""
import pytest
from src.connectors.solana_rpc import SolanaRPCConnector
from src.connectors.jupiter_dex import JupiterDEXConnector
from src.connectors.spl_token import SPLTokenConnector, KNOWN_MINTS


class TestSolanaRPCConnector:
    def setup_method(self):
        self.rpc = SolanaRPCConnector(rpc_url="https://api.devnet.solana.com")

    def test_initialization(self):
        assert "devnet" in self.rpc.rpc_url

    def test_health_check(self):
        assert self.rpc.health_check() is True

    def test_get_balance_returns_stub(self):
        result = self.rpc.get_balance("11111111111111111111111111111111")
        assert result["_stub"] is True
        assert result["method"] == "getBalance"

    def test_get_slot_returns_stub(self):
        result = self.rpc.get_slot()
        assert result["_stub"] is True
        assert result["method"] == "getSlot"

    def test_send_transaction_returns_stub(self):
        result = self.rpc.send_transaction("FAKE_TX_BASE64")
        assert result["method"] == "sendTransaction"

    def test_get_transaction_returns_stub(self):
        result = self.rpc.get_transaction("FAKE_SIG")
        assert result["method"] == "getTransaction"


class TestJupiterDEXConnector:
    def setup_method(self):
        self.jup = JupiterDEXConnector(slippage_bps=50)

    def test_initialization(self):
        assert self.jup.slippage_bps == 50

    def test_health_check(self):
        assert self.jup.health_check() is True

    def test_get_quote_returns_expected_fields(self):
        quote = self.jup.get_quote(
            KNOWN_MINTS["SOL"], KNOWN_MINTS["USDC"], 1_000_000
        )
        assert "outAmount" in quote
        assert "priceImpactPct" in quote
        assert quote["amount"] == 1_000_000

    def test_out_amount_less_than_in(self):
        quote = self.jup.get_quote(KNOWN_MINTS["SOL"], KNOWN_MINTS["USDC"], 1_000_000)
        assert quote["outAmount"] < quote["amount"]

    def test_build_swap_transaction(self):
        quote = self.jup.get_quote(KNOWN_MINTS["SOL"], KNOWN_MINTS["USDC"], 1_000_000)
        tx = self.jup.build_swap_transaction(quote, "USER_PUBKEY_STUB")
        assert "swapTransaction" in tx
        assert tx["userPubkey"] == "USER_PUBKEY_STUB"


class TestSPLTokenConnector:
    def setup_method(self):
        self.spl = SPLTokenConnector()

    def test_health_check(self):
        assert self.spl.health_check() is True

    def test_resolve_known_mint_usdc(self):
        assert self.spl.resolve_mint("USDC") == KNOWN_MINTS["USDC"]

    def test_resolve_known_mint_sol(self):
        assert self.spl.resolve_mint("SOL") == KNOWN_MINTS["SOL"]

    def test_resolve_unknown_mint_returns_none(self):
        assert self.spl.resolve_mint("FAKECOIN") is None

    def test_get_token_balance_stub(self):
        result = self.spl.get_token_balance("FAKE_TOKEN_ACCOUNT")
        assert result["_stub"] is True

    def test_get_mint_info_stub(self):
        result = self.spl.get_mint_info(KNOWN_MINTS["USDC"])
        assert result["_stub"] is True
