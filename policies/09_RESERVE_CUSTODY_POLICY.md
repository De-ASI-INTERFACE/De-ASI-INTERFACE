# Reserve Custody Policy

**Entity:** De-ASI-INTERFACE / QuantumTradingInfinity / richy.ai  
**Author:** Richard Patterson ([@De-ASI-INTERFACE](https://github.com/De-ASI-INTERFACE))  
**Effective Date:** July 1, 2026  
**Classification:** Institutional · Confidential  
**Version:** 1.0.0

---

## 1. Purpose

This policy establishes binding operational procedures for the management, segregation, and time-locked cold custody of all institutional reserve assets held across the De-ASI-INTERFACE ecosystem. It governs SOL, SPL tokens (including LWC and $KATCOIN), and any protocol-native treasury assets deployed or custodied on Solana Mainnet.

---

## 2. Scope

This policy applies to:
- All on-chain wallet addresses designated as institutional reserves
- All program-derived addresses (PDAs) holding treasury or protocol-fee assets
- All multisig custody accounts governing reserve capital
- The `rp_spl_amm_platform_v1` UBI treasury fee accumulator
- The `lwc-utility-token` staking and governance treasury

---

## 3. Cold Custody Classification

Institutional reserves are classified into three custody tiers:

| Tier | Type | Access Control | Unlock Mechanism |
|---|---|---|---|
| Tier 1 — Deep Cold | Hardware wallet (air-gapped) | Single authorized signatory | Manual, offline signing only |
| Tier 2 — Multisig Cold | Squads Protocol v4 multisig | M-of-N threshold (min 2-of-3) | On-chain proposal + time delay |
| Tier 3 — Time-Locked PDA | On-chain program account | Program authority (cold) | `Clock::unix_timestamp` constraint |

---

## 4. Time-Lock Requirements

All Tier 2 and Tier 3 reserve accounts **must** enforce the following minimum time-lock windows before any disbursement or transfer instruction can execute:

- **Operating Reserve (≤ 10% of total):** Minimum 48-hour time-lock
- **Protocol Treasury (10–40% of total):** Minimum 7-day time-lock
- **Institutional Reserve (> 40% of total):** Minimum 30-day time-lock
- **Emergency Reserve:** Minimum 90-day time-lock; requires 3-of-3 multisig approval

No exception to time-lock windows is permitted without a formal governance proposal recorded on-chain and in this repository.

---

## 5. Key Custody Controls

- **Private key segregation:** Reserve wallet private keys are never stored in `.env` files, hot wallets, or any internet-connected environment.
- **No programmatic access:** Reserve accounts are never referenced as signers in any automated trading bot, API, or CI/CD pipeline.
- **Air-gap signing:** Tier 1 transactions are signed exclusively on an offline device and broadcast separately.
- **Multisig quorum:** Tier 2 disbursements require a minimum 2-of-3 quorum with a 24-hour execution delay after proposal approval.
- **On-chain audit trail:** All reserve movements generate on-chain transaction records cross-referenced in `AUDIT_REPORT.md`.

---

## 6. Reserve Segregation

Institutional reserves are strictly segregated from:
- Trading capital deployed in `trading-bot` or `solana-execution`
- Liquidity pool deposits in `rp_spl_amm_platform_v1`
- Operational hot wallets used for gas/fee payments
- Any wallet address used as a program authority in active development

---

## 7. Proof-of-Reserves Attestation

A reserve manifest (`docs/RESERVE_MANIFEST.md`) is maintained and updated no less than quarterly. Each entry in the manifest includes:
- Wallet address or PDA
- Asset type and denomination
- Custody tier classification
- Lock expiry timestamp (Unix + human-readable)
- Controlling authority (multisig address or hardware wallet fingerprint hash)

The manifest is cryptographically linked to `AUDIT_REPORT.md` upon each quarterly attestation cycle.

---

## 8. Incident and Breach Protocol

Any unauthorized access attempt, key compromise, or unplanned reserve movement triggers immediate escalation per `policies/08_INCIDENT_RESPONSE_POLICY.md`. Reserve accounts are to be considered compromised if any signing key associated with them is exposed to an internet-connected environment for any duration.

---

## 9. Regulatory Alignment

This policy is designed to align with institutional best practices consistent with:
- SEC guidance on digital asset custody (2025 Staff Bulletin)
- FinCEN AML program requirements (cross-referenced: `07_ANTI_MONEY_LAUNDERING_POLICY.md`)
- FATF Travel Rule obligations for transfers above reporting thresholds
- Ohio financial services regulatory framework for digital asset entities

---

## 10. Review Cycle

This policy is reviewed and re-attested **quarterly** (January, April, July, October) or immediately following any material change to reserve balances exceeding 15% of total institutional capital.

---

*Policy Owner: Richard Patterson · De-ASI-INTERFACE · Akron, Ohio*  
*Next Review: October 1, 2026*
