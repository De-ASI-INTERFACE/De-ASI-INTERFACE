# Change Management and Segregation of Duties Policy

**Organization:** De-ASI-INTERFACE
**Document ID:** POLICY-011
**Version:** 1.0.0
**Effective Date:** September 10, 2026
**Classification:** Confidential — Internal Use Only
**Owner:** Richard Patterson

---

## 1. Purpose

This policy defines who may make what change to which system, how the change is proposed, reviewed, approved, deployed, and audited. It establishes segregation of duties (SoD) sufficient to prevent any single actor from committing, approving, deploying, and executing a change that moves value or alters trust-relevant infrastructure without an independent check.

Effective from the date above, this policy supersedes any prior informal practice. Where prior practice differed, the effective date governs; no representation is made about the state of controls prior to that date.

---

## 2. Scope

This policy governs changes to:

- Any repository under [@De-ASI-INTERFACE](https://github.com/De-ASI-INTERFACE) whose code, configuration, or infrastructure can (a) sign a transaction, (b) route trading orders, (c) change trust boundaries, or (d) alter policies in this suite.
- Multisig membership, quorum, or execution parameters on any Squads Protocol account referenced in POLICY-009.
- Signing keys and their custody arrangements.
- CI/CD pipeline configuration, GitHub Actions secrets, and any credential that grants deploy or release rights.

Documentation-only changes and dependency-bump changes that touch no in-scope path are out of scope.

---

## 3. Change Classes

| Class | Examples | Approval required |
|---|---|---|
| CM-1 Standard | Refactor, non-functional docs, comment edits, added tests | PR from a branch, self-review permitted for the sole maintainer, must pass CI |
| CM-2 Reviewed | Any change to `apps/`, `packages/`, `src/`, `programs/`, or agent inventory files | PR from a branch, CODEOWNERS review required, must pass CI |
| CM-3 Elevated | Kill-switch code paths, signing paths, RPC-endpoint configuration, dependency upgrades on cryptographic libraries | PR from a branch, CODEOWNERS review, reviewer distinct from author, must pass CI + security scans, 24-hour minimum in-review window |
| CM-4 Trusted | Multisig membership or quorum change, key rotation on a hot wallet, policy suite edits, treasury address change | PR from a branch, CODEOWNERS review, out-of-band written approval from the policy owner recorded in the PR, must pass CI |
| CM-5 Reserve | Any change touching a Tier 1–3 reserve account per POLICY-009 | Off-repository governance proposal per POLICY-009 §4, not merged as code |

Where a change spans multiple classes, the highest class governs.

---

## 4. Segregation of Duties (Sole-Operator Adaptation)

The entity currently operates with a single natural-person principal. Ideal SoD requires distinct author, reviewer, approver, and executor. Until the entity has additional personnel, the following compensating controls apply and are the honest statement of practice:

- CM-3 and above may not be self-approved. If no independent reviewer is available, the change is either (a) deferred until one is available, or (b) merged with an explicit "sole-operator exception" note in the PR, filed against a running exception log at `policies/inventory/sole-operator-exceptions.md`. The exception log is reviewed at each policy review cycle.
- CM-4 changes may not use the sole-operator exception. They require an out-of-band reviewer engaged for that change.
- CM-5 changes are governed by POLICY-009 and are not subject to the sole-operator exception under any circumstance.

This is a compensating control, not equivalence to real SoD. The exception log is deliberately visible and reviewable.

---

## 5. Repository Controls

The following controls are enforced at the GitHub repository level and are considered part of this policy:

- `main` is protected: linear history, no force-push, no deletion.
- All merges to `main` require a pull request.
- Pull requests to `main` require at least one CODEOWNERS review and require the last push to be approved (dismissing stale reviews on new commits).
- Signed commits are required on `main`. Commit signatures use a hardware-backed key where feasible.
- Administrator bypass of protection is permitted for the sole principal, is logged by GitHub, and any use of bypass is recorded within 24 hours in `policies/inventory/sole-operator-exceptions.md`.
- Required conversation resolution is enabled: unresolved review threads block merge.
- Dependabot security updates and vulnerability alerts are enabled.

---

## 6. Deployment and Release

- Release tags are signed.
- Deployments to production are gated on a successful release build and on the presence of a matching validation record for any AI agent whose behavior the release changes (see POLICY-010 §6).
- Kill-switch responsiveness is smoke-tested as part of the release pipeline; a release that fails the kill-switch smoke test does not proceed to production.
- Rollback procedure is documented in the deployment runbook and rehearsed at least quarterly.

---

## 7. Credential and Secret Handling

- CI secrets are scoped to the minimum required job.
- Long-lived credentials are inventoried in `policies/inventory/credentials.md` (metadata only; secrets never appear in the repository).
- Rotation cadence is defined in the compliance calendar (`policies/COMPLIANCE_CALENDAR.md`).
- Any credential known or suspected to have been exposed triggers an incident under POLICY-008 within one hour.

---

## 8. Review and Owner

This policy is reviewed at least annually and upon any material operational change. The next scheduled review date is September 10, 2027. The policy owner is Richard Patterson.

*Verified and approved by Richard Patterson — September 10, 2026*
