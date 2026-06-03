# Security Policy

## Supported Versions

Only the latest version on the `Richy` branch is actively maintained and eligible for security fixes.

| Branch | Supported |
|--------|----------|
| `Richy` (latest) | ✅ Yes |
| All others | ❌ No |

---

## Reporting a Vulnerability

**Do not open a public GitHub issue for security vulnerabilities.**

Public disclosure before a coordinated fix puts users at risk and will not be acknowledged or rewarded.

### How to Report

Report security vulnerabilities privately via:
- **GitHub Private Security Advisory** (preferred): [Security Advisories](https://github.com/De-ASI-INTERFACE/De-ASI-INTERFACE/security/advisories/new)
- **Direct message on X/Twitter**: [@De-ASI-INTERFACE](https://x.com)

Include in your report:
- A clear description of the vulnerability
- Steps to reproduce
- Potential impact
- Any suggested mitigations if known

---

## Coordinated Disclosure Policy

- You will receive an acknowledgment within **72 hours**
- We will investigate and communicate a timeline for a fix
- **No public disclosure** until a patch is released and deployed
- We reserve the right to determine the severity and fix timeline
- Responsible disclosures will be credited in the release notes (if desired)

---

## Scope

In scope:
- This repository and its code
- Dependencies introduced by this project
- Deployed infrastructure directly managed by this project

Out of scope:
- Third-party services, APIs, or platforms this project integrates with
- Issues in upstream dependencies (report those to the upstream maintainer)
- Social engineering or phishing attacks

---

## Security Practices in This Codebase

- All secrets are loaded from environment variables — never hardcoded
- All commits are GPG-signed
- Dependencies are pinned to verified versions
- No unvetted GitHub Actions or third-party apps are authorized

---

*De-ASI-INTERFACE Security Policy — maintained by Richard Patterson*
