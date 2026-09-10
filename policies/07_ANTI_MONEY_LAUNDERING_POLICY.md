# Anti-Money Laundering (AML) & Know Your Customer (KYC) Policy

**Organization:** De-ASI-INTERFACE  
**Document ID:** POLICY-007  
**Version:** 1.0.0  
**Effective Date:** June 6, 2026  
**Classification:** Confidential  
**Owner:** Richard Patterson  

---

## 1. Purpose

This AML/KYC Policy establishes procedures and controls to detect, prevent, and report activities that may involve money laundering, terrorist financing, or other financial crimes. This policy reflects a commitment to U.S. federal law compliance and international financial standards.

Effective from the date above, this policy supersedes any prior informal practice. Where prior practice differed, the effective date governs; no representation is made about the state of controls prior to that date.

---

## 2. Regulatory Status (Pending Counsel Review)

De-ASI-INTERFACE operates as a software developer entity. Whether it is a Money Services Business (MSB) subject to FinCEN registration under 31 CFR 1010.100(ff), or a money transmitter under Ohio Revised Code Chapter 1315, is a fact-specific determination that turns on whether the entity accepts and transmits third-party value, takes custody of user funds, or operates a hosted exchange or wallet on behalf of others. As of the effective date above, this determination is pending counsel review.

Until that review completes, this policy is a statement of intended control posture, not an assertion that the entity is a registered MSB or licensed money transmitter. No statement in this document should be read as a representation that De-ASI-INTERFACE has completed FinCEN Form 107 registration or holds any state money transmitter license. If the counsel review concludes that registration or licensure is required, the entity will complete it before commencing any activity that would trigger the requirement.

## 3. Regulatory Framework Informing This Policy

This policy is informed by, and aims to be defensible under, the following even where formal registration is not required:
- U.S. Bank Secrecy Act (BSA)
- FinCEN guidance on virtual currency, including [FIN-2019-G001](https://www.fincen.gov/sites/default/files/2019-05/FinCEN%20Guidance%20CVC%20FINAL%20508.pdf)
- FATF (Financial Action Task Force) Recommendations
- Treasury Department OFAC sanctions compliance (which applies to all U.S. persons irrespective of MSB status)

---

## 4. KYC Procedures

- Identity verification required before fiat on/off-ramp access
- Users from OFAC-sanctioned jurisdictions blocked at the protocol level
- Wallet screening performed against illicit address databases (Chainalysis, TRM Labs)

---

## 5. Transaction Monitoring

- Automated monitoring flags transactions exceeding $10,000 equivalent within 24 hours
- Structuring patterns trigger enhanced review
- Wallets associated with mixer services, darknet markets, or ransomware are blacklisted

---

## 6. Suspicious Activity Reporting

Where the entity is legally required to file a Suspicious Activity Report (SAR) under 31 CFR 1022.320 or a successor rule (a determination that presupposes MSB status per Section 2 above), such reports will be filed with FinCEN within the statutory window. Internal escalation of suspicious activity occurs within 24 hours in all cases, regardless of whether a SAR filing obligation attaches. Records of internal escalations and any filed SARs are maintained for a minimum of 5 years.

---

## 7. Sanctions Compliance

- Real-time OFAC sanctions list screening applied to all wallet interactions
- No services provided to sanctioned individuals, entities, or jurisdictions
- Violations reported to relevant regulatory authority immediately

---

*Document verified and approved by Richard Patterson — June 6, 2026*
