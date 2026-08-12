# Institutional Reserve Manifest

**Entity:** De-ASI-INTERFACE / QuantumTradingInfinity / richy.ai  
**Manifest Version:** 1.0.0  
**Attestation Date:** July 1, 2026  
**Classification:** Institutional · Internal  
**Governing Policy:** [`policies/09_RESERVE_CUSTODY_POLICY.md`](../policies/09_RESERVE_CUSTODY_POLICY.md)

> ⚠️ **Notice:** Wallet addresses and specific balances are redacted in this public-facing manifest. Full attestation records, including on-chain transaction signatures and balance snapshots, are maintained in the private audit ledger and cross-referenced in `AUDIT_REPORT.md`.

---

## Reserve Account Registry

| Account ID | Asset Type | Custody Tier | Lock Duration | Lock Expiry (UTC) | Authority Type | Status |
|---|---|---|---|---|---|---|
| RESERVE-001 | SOL | Tier 1 — Deep Cold | 30 days | Rolling · 30-day reset | Hardware wallet (air-gapped) | 🔒 LOCKED |
| RESERVE-002 | LWC SPL Token | Tier 3 — Time-Locked PDA | 90 days | 2026-09-29 00:00 UTC | Program PDA · Cold authority | 🔒 LOCKED |
| RESERVE-003 | $KATCOIN SPL Token | Tier 2 — Multisig Cold | 30 days | 2026-07-31 00:00 UTC | Squads v4 · 2-of-3 | 🔒 LOCKED |
| RESERVE-004 | USDC (Operational Reserve) | Tier 2 — Multisig Cold | 7 days | Rolling · 7-day reset | Squads v4 · 2-of-3 | 🔒 LOCKED |
| RESERVE-005 | AMM Treasury Fees (SOL) | Tier 3 — Time-Locked PDA | 7 days | Rolling · 7-day reset | rp_spl_amm PDA | 🔒 LOCKED |
| RESERVE-006 | Emergency Reserve (SOL) | Tier 1 — Deep Cold | 90 days | 2026-09-29 00:00 UTC | Hardware wallet (air-gapped) | 🔒 LOCKED |

---

## Custody Tier Legend

| Tier | Description | Unlock Process |
|---|---|---|
| Tier 1 — Deep Cold | Air-gapped hardware wallet; never internet-connected | Manual offline signing only |
| Tier 2 — Multisig Cold | Squads Protocol v4; minimum 2-of-3 quorum | On-chain proposal + 24h execution delay |
| Tier 3 — Time-Locked PDA | Solana program-derived address with `Clock` constraint | Program instruction after `unix_timestamp` expiry |

---

## Segregation Attestation

As of this attestation date, all accounts listed above are confirmed:

- ✅ **Segregated** from all active trading wallets and hot operational wallets
- ✅ **Not referenced** as signers in any automated system (`trading-bot`, `solana-execution`, CI/CD pipelines)
- ✅ **Time-lock constraints active** and verifiable on Solana Mainnet via on-chain account state
- ✅ **No outstanding unsigned disbursement proposals** pending against any reserve account
- ✅ **AML screening current** — all counterparty addresses in prior reserve movements are sanctions-screened per `07_ANTI_MONEY_LAUNDERING_POLICY.md`

---

## Quarterly Attestation Log

| Quarter | Date | Attesting Officer | Audit Reference | Status |
|---|---|---|---|---|
| Q3 2026 | July 1, 2026 | Richard Patterson | `AUDIT_REPORT.md · §Reserve-Q3-2026` | ✅ Attested |
| Q4 2026 | October 1, 2026 | — | Pending | ⏳ Scheduled |

---

## On-Chain Verification

All Tier 2 and Tier 3 accounts are verifiable on-chain via Solana Mainnet explorers:
- [Solana Explorer](https://explorer.solana.com)
- [Solscan](https://solscan.io)
- [SolanaFM](https://solana.fm)

Time-lock expiry for PDAs can be verified by querying the account data field `unlock_timestamp` against current `Clock::unix_timestamp`.

---

## Compliance Cross-References

- [`policies/09_RESERVE_CUSTODY_POLICY.md`](../policies/09_RESERVE_CUSTODY_POLICY.md) — governing custody policy
- [`policies/07_ANTI_MONEY_LAUNDERING_POLICY.md`](../policies/07_ANTI_MONEY_LAUNDERING_POLICY.md) — AML obligations
- [`policies/08_INCIDENT_RESPONSE_POLICY.md`](../policies/08_INCIDENT_RESPONSE_POLICY.md) — breach escalation
- [`AUDIT_REPORT.md`](../AUDIT_REPORT.md) — full audit attestation record

---

*Manifest Owner: Richard Patterson · De-ASI-INTERFACE · Akron, Ohio*  
*Next Attestation: October 1, 2026*
