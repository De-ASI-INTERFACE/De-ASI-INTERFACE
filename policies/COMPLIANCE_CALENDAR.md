# Compliance Calendar

**Organization:** De-ASI-INTERFACE
**Document ID:** POLICY-CAL
**Version:** 1.0.0
**Effective Date:** September 10, 2026
**Classification:** Confidential — Internal Use Only
**Owner:** Richard Patterson

---

## Purpose

This calendar is the single source of truth for recurring obligations, review dates, and rotation cadences arising from the policy suite. Every row has an owner, a cadence, a due date derived from that cadence, and a link to the policy that requires it. If an obligation is not on this list, it does not exist as an obligation. Adding an obligation requires a PR that also adds it here.

The next full review of this calendar is September 10, 2027.

---

## One-Time Obligations Currently Open

| # | Obligation | Policy | Owner | Target date | Status |
|---|---|---|---|---|---|
| O1 | Engage counsel for MSB / Ohio money-transmitter determination per POLICY-007 §2 | 07 | Principal | Before any activity that could trigger MSB status | Open |
| O2 | Complete and publish the AI agent inventory (`policies/inventory/agents.yaml`) before any A2+ agent runs in production | 10 §3 | Principal | Before first A2+ deployment | Open |
| O3 | Complete kill-switch implementation and record baseline SLO measurement | 03 §5, 08 §3 | Principal | Before first live-capital deployment | Open |
| O4 | Complete decision-audit-log implementation and verifier | 10 §8 | Principal | Before first live-capital deployment | Open |
| O5 | Complete SBOM generation and publish for every tagged release | 11 §5 | Principal | Next release after CI hardening lands | Open |

---

## Recurring Obligations

| # | Obligation | Policy | Owner | Cadence | Next due |
|---|---|---|---|---|---|
| R1 | Policy suite annual review | All | Principal | Annual | 2027-09-10 |
| R2 | AI agent independent validation per in-scope agent | 10 §6 | Reviewer | Every 90 days per agent | Per agent, tracked in `policies/inventory/validation-log.md` |
| R3 | Kill-switch drill (measured against POLICY-003 §5 SLO) | 03 §5, 08 §3 | Principal | Quarterly | 2026-12-10 |
| R4 | Rollback drill on production release pipeline | 11 §6 | Principal | Quarterly | 2026-12-10 |
| R5 | Dependency audit (`pnpm audit`, `cargo audit`, Python `pip-audit`) | 11 | Principal | Weekly (automated) + review any high/critical within 72 hours | Continuous |
| R6 | SBOM regeneration on every tagged release | 11 §5 | Principal | Per release | On release |
| R7 | OFAC SDN list refresh check for any wallet-screening tooling (if wired) | 07 §7 | Principal | Weekly | Continuous |
| R8 | Hot-wallet key rotation | 09, 11 §7 | Principal | Every 90 days | 2026-12-10 |
| R9 | Multisig membership review | 09 §5 | Principal | Every 180 days | 2027-03-10 |
| R10 | Time-lock parameter review on Tier 2 and Tier 3 reserves | 09 §4 | Principal | Every 180 days | 2027-03-10 |
| R11 | Incident-response tabletop exercise (P0 scenario) | 08 | Principal | Every 180 days | 2027-03-10 |
| R12 | Sole-operator exception log review (per POLICY-011 §4) | 11 §4 | Principal | Every 90 days | 2026-12-10 |
| R13 | Credential inventory reconciliation against GitHub Actions secrets and hosted-provider credentials | 11 §7 | Principal | Every 90 days | 2026-12-10 |
| R14 | Backdated-attestation audit: grep the repo for language that overstates the history of controls | 07, 11 | Principal | Every policy PR + quarterly | 2026-12-10 |

---

## How to Use This Calendar

- Every recurring obligation in Section 3 is treated as a scheduled task. When a task runs, its `Next due` date is bumped by the cadence and the run is recorded (a short note in the PR that updates this file is sufficient).
- Missing an obligation is itself an incident under POLICY-008 §2 at classification P2 unless the miss creates active regulatory or financial exposure, in which case it is P1.
- Every open one-time obligation in Section 2 blocks any activity gated on it. Closing an obligation requires a PR that moves the row into a closed-obligations appendix, with the closing evidence linked.

---

*Verified and approved by Richard Patterson — September 10, 2026*
