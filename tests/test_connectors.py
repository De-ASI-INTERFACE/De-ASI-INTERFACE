"""Tests — Solana Trading and DeFi Connectors
Owner/Creator: Richard Patterson | © 2026 Richard Patterson
"""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).parents[1]))

import pytest
from src.connectors.solana_rpc import SolanaRPCConnector
from src.connectors.jupiter_dex import JupiterDEXConnector
from src.connectors.spl_token import SPLTokenConnector, KNOWN_MINTS


class TestSolanaRPCConnector:
    def setup_method(self):
        self.rpc = SolanaRPCConnector(rpc_url="https://api.devnet.solana.com")

    def test_init(self):
        assert "devnet" in self.rpc.rpc_url

    def test_health(self):
        assert self.rpc.health_check()

    def test_get_balance_stub(self):
        r = self.rpc.get_balance("11111111111111111111111111111111")
        assert r["_stub"] is True and r["method"] == "getBalance"

    def test_get_slot_stub(self):
        r = self.rpc.get_slot()
        assert r["_stub"] is True and r["method"] == "getSlot"

    def test_send_transaction_stub(self):
        r = self.rpc.send_transaction("FAKE_TX")
        assert r["method"] == "sendTransaction"

    def test_get_transaction_stub(self):
        r = self.rpc.get_transaction("FAKE_SIG")
        assert r["method"] == "getTransaction"

    def test_result_key_present(self):
        r = self.rpc.get_slot()
        assert "result" in r

    def test_jsonrpc_version(self):
        r = self.rpc.get_slot()
        assert r["jsonrpc"] == "2.0"

    def test_default_rpc_url(self):
        rpc = SolanaRPCConnector()
        assert "solana.com" in rpc.rpc_url


class TestJupiterDEXConnector:
    def setup_method(self):
        self.jup = JupiterDEXConnector(slippage_bps=50)

    def test_init(self):
        assert self.jup.slippage_bps == 50

    def test_health(self):
        assert self.jup.health_check()

    def test_quote_fields(self):
        q = self.jup.get_quote(KNOWN_MINTS["SOL"], KNOWN_MINTS["USDC"], 1_000_000)
        assert "outAmount" in q and "priceImpactPct" in q

    def test_out_less_than_in(self):
        q = self.jup.get_quote(KNOWN_MINTS["SOL"], KNOWN_MINTS["USDC"], 1_000_000)
        assert q["outAmount"] < q["amount"]

    def test_slippage_in_quote(self):
        q = self.jup.get_quote(KNOWN_MINTS["SOL"], KNOWN_MINTS["USDC"], 1_000_000)
        assert q["slippageBps"] == 50

    def test_build_swap_tx(self):
        q  = self.jup.get_quote(KNOWN_MINTS["SOL"], KNOWN_MINTS["USDC"], 1_000_000)
        tx = self.jup.build_swap_transaction(q, "USER_PUBKEY")
        assert "swapTransaction" in tx and tx["userPubkey"] == "USER_PUBKEY"

    def test_stub_flag(self):
        q = self.jup.get_quote(KNOWN_MINTS["SOL"], KNOWN_MINTS["USDC"], 500)
        assert q["_stub"] is True


class TestSPLTokenConnector:
    def setup_method(self):
        self.spl = SPLTokenConnector()

    def test_health(self):
        assert self.spl.health_check()

    def test_resolve_usdc(self):
        assert self.spl.resolve_mint("USDC") == KNOWN_MINTS["USDC"]

    def test_resolve_sol(self):
        assert self.spl.resolve_mint("SOL") == KNOWN_MINTS["SOL"]

    def test_resolve_bonk(self):
        assert self.spl.resolve_mint("BONK") == KNOWN_MINTS["BONK"]

    def test_resolve_unknown(self):
        assert self.spl.resolve_mint("FAKECOIN") is None

    def test_resolve_case_insensitive(self):
        assert self.spl.resolve_mint("usdc") == KNOWN_MINTS["USDC"]

    def test_get_token_balance_stub(self):
        r = self.spl.get_token_balance("FAKE_ACCT")
        assert r["_stub"] is True

    def test_get_mint_info_stub(self):
        r = self.spl.get_mint_info(KNOWN_MINTS["USDC"])
        assert r["_stub"] is True
