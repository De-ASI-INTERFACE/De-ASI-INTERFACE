# AI Agent Governance Policy

**Organization:** De-ASI-INTERFACE
**Document ID:** POLICY-010
**Version:** 1.0.0
**Effective Date:** September 10, 2026
**Classification:** Confidential — Internal Use Only
**Owner:** Richard Patterson

---

## 1. Purpose

This policy establishes the governance framework for AI agents that make autonomous decisions capable of moving on-chain value, sending transactions, or altering protocol state. It aligns operational practice with the model risk management principles in [Federal Reserve SR 11-7 / OCC Bulletin 2011-12](https://www.federalreserve.gov/supervisionreg/srletters/sr1107a1.pdf) and the risk management functions of the [NIST AI Risk Management Framework (AI RMF 1.0)](https://www.nist.gov/itl/ai-risk-management-framework), adapted for a small, non-institutional operator running Solana-native agentic finance.

Effective from the date above, this policy supersedes any prior informal practice. Where prior practice differed, the effective date governs; no representation is made about the state of controls prior to that date.

---

## 2. Scope

This policy applies to every software agent that:

- Holds or can request signing authority over any wallet controlled by the entity,
- Can invoke any tool that emits a Solana transaction, EVM transaction, exchange order, or off-chain payment, or
- Can autonomously alter protocol state, treasury allocation, or user-facing configuration.

Read-only research agents, chat agents, and code-generation agents are out of scope unless one of the above conditions attaches.

---

## 3. Model Inventory

Every in-scope agent is recorded in a versioned inventory file at `policies/inventory/agents.yaml` in this repository. Each entry captures, at minimum:

- Agent name and canonical identifier
- Deployment environment (dev / staging / production)
- Underlying model provider, model family, and pinned model version
- System prompt hash (SHA-256 of the frozen system prompt at release time)
- Tool set (enumerated by tool identifier)
- Signing authority scope (which wallets, which programs, which instruction types)
- Owner (a natural person)
- Reviewer (a natural person distinct from the owner)
- Last independent validation date
- Kill-switch identifier (from POLICY-008 §3)

No in-scope agent may be deployed to production without a complete inventory entry.

---

## 4. Authority Matrix

Agent authority is expressed as an explicit matrix, not as a default. Each agent has a per-transaction cap, a per-hour cap, and a per-day cap, denominated in USD-equivalent notional value at the time of the transaction. Caps are enforced at the signing layer (see POLICY-009 §5 on non-programmatic access to reserve wallets and the runtime enforcement contract in the Cl-eveland kill-switch design).

| Authority tier | Per-tx cap | Per-hour cap | Per-day cap | Human approval |
|---|---|---|---|---|
| A0 — Read only | n/a | n/a | n/a | Not required |
| A1 — Simulated | Simulation only, no broadcast | n/a | n/a | Not required |
| A2 — Micro | $50 | $250 | $1,000 | Post-hoc review |
| A3 — Bounded | $500 | $2,500 | $10,000 | Human-in-loop above $1,000 in a single decision |
| A4 — Elevated | $5,000 | $25,000 | $100,000 | Human-in-loop for every transaction; two-person rule |
| A5 — Reserve | n/a | n/a | n/a | Prohibited for agents; see POLICY-009 |

New agents start at A0 and must accumulate a documented validation history to advance a tier. Tier advancement requires the reviewer's approval recorded in the inventory entry.

---

## 5. Human-in-the-Loop

For any decision that exceeds a per-decision USD threshold specified in the agent's tier row, the agent must emit a proposal (not a transaction), block on human approval, and only broadcast after a signed approval is received via the change-management path defined in POLICY-011. The proposal record and the approval record are both retained in the decision audit log described in Section 8.

---

## 6. Independent Validation

Before any in-scope agent is deployed to production, and at least every 90 days thereafter, the agent is validated by a reviewer distinct from its owner. Validation covers, at a minimum:

- Behavior on a fixed evaluation corpus, including adversarial prompts specific to the agent's tool set
- Refusal behavior on out-of-scope requests (attempted authority escalation, attempted use of prohibited tools, attempted access to reserve wallets)
- Kill-switch responsiveness measured against the SLO in POLICY-003 §5
- Consistency of decisions against a golden set (reproducibility check)

Validation results are recorded in `policies/inventory/validation-log.md` with the date, reviewer, model version, corpus hash, and pass/fail per criterion.

---

## 7. Change Control

Any change to any of the following requires the change-management path in POLICY-011:

- The agent's model provider or pinned model version
- The agent's system prompt
- The agent's tool set
- The agent's authority tier
- The agent's signing scope

Silent updates (for example, a provider updating a model weight behind an unchanged endpoint identifier) are treated as changes and require re-validation before the agent continues to operate in production. Model providers whose endpoints do not offer a stable version pin are not eligible for use in tiers A3 and above.

---

## 8. Decision Audit Log

Every in-scope agent decision produces an append-only, hash-chained audit record. The design and storage contract for this log is specified in the Cl-eveland platform reference documentation (see the decision-audit RFC linked from the deployment runbook). Each record includes, at minimum: timestamp, agent identifier, model provider, pinned model version, system prompt hash, input hash, tool call sequence with responses, RPC responses relied upon, decision, proposal-versus-broadcast flag, human approval reference if applicable, resulting transaction signature if any, and the hash of the prior record. The log is verifiable end-to-end and is the primary evidence source for post-incident review under POLICY-008 §5.

---

## 9. Prohibited Uses

Under this policy, an in-scope agent may not:

- Hold signing authority over any Tier 1, Tier 2, or Tier 3 reserve account defined in POLICY-009 §3.
- Be granted authority to modify its own inventory entry, its own system prompt, its own tool set, or its own authority tier.
- Be operated in production without an active kill switch and an in-date validation record.
- Be operated in production against a model endpoint that does not support a stable, pinned version identifier for authority tiers A3 and above.

---

## 10. Review and Owner

This policy is reviewed at least annually and upon any material change to the agent runtime, tool set, or regulatory framework. The next scheduled review date is September 10, 2027. The policy owner is Richard Patterson.

*Verified and approved by Richard Patterson — September 10, 2026*
