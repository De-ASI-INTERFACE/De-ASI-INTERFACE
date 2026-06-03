# Contributing to De-ASI-INTERFACE

Thank you for your interest in this project. Before contributing, read this document in full. By submitting a pull request or issue, you agree to the terms below.

---

## Ground Rules

1. **All pull requests must reference an open issue.**
   - Open an issue first. Describe the problem or feature. Wait for acknowledgment before writing code.
   - PRs submitted without a linked issue will be closed without review.

2. **All commits must be GPG-signed.**
   - Unsigned commits will not be merged. No exceptions.
   - See: https://docs.github.com/en/authentication/managing-commit-signature-verification

3. **No dependencies from untrusted or unaudited sources.**
   - Every new dependency must be justified in the PR description.
   - Dependencies must be pinned to an exact version and verified hash.
   - Package sources must be from official registries (npm, PyPI, crates.io).
   - No dependencies from personal forks, unknown publishers, or unverified GitHub repos.

4. **Code review is mandatory.**
   - All changes require at least one approved review before merge.
   - Reviews are not guaranteed. PRs may be closed at any time without explanation.

5. **The maintainer reserves the right to reject or close any PR without explanation.**
   - This is not subject to appeal. Contributions are a privilege, not a right.

---

## Pull Request Process

1. Fork the repo and create a feature branch from `Richy`
2. Write your changes with clear, minimal commits
3. Sign all commits with GPG
4. Open a PR referencing the issue number (e.g., `Closes #12`)
5. Describe what changed, why, and how it was tested
6. Wait for review — do not ping or bump unless 14+ days have passed

---

## Code Standards

- Python: PEP 8 compliant
- TypeScript/JavaScript: ESLint + Prettier enforced
- No commented-out code in final PRs
- No debug logs, console.log, or print statements in production paths
- All secrets must be loaded from environment variables — never hardcoded

---

## What Will Be Rejected Immediately

- PRs with unsigned commits
- PRs that introduce unvetted dependencies
- PRs with hardcoded credentials, keys, or tokens
- PRs that modify CI/CD or GitHub Actions workflows without explicit prior approval
- PRs from bots or automated tools not explicitly invited

---

## Legal

By submitting a contribution, you affirm that:
- You have the right to submit the code
- The contribution is your original work or properly attributed
- You grant the maintainer a perpetual, irrevocable license to use, modify, and distribute your contribution under the project license

The maintainer reserves all rights to this codebase. Community contributions do not grant ownership, governance rights, or financial claims.

---

*De-ASI-INTERFACE is maintained by Richard Patterson. Built in Ohio.*
