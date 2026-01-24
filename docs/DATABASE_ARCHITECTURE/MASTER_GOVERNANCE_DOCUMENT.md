# Master Database Architecture, Hardening, Governance, and Compliance Document
## Accounting Platform – PostgreSQL (UK / FCA / SaaS Context)

Audience:
- Database Administrator (DBA)
- Database architect / implementer
- Senior backend engineers
- Security, risk, and compliance stakeholders
- SaaS platform owners

This document is the **single authoritative reference** for database design, enforcement, governance, regulatory alignment, and SaaS-readiness. It consolidates all architectural decisions, audits, controls, and forward-looking compliance measures into one artifact.

---

## 1. Executive Summary

This database underpins a financial SaaS platform operating in a UK regulatory context. As such, it must satisfy not only functional requirements but also **data integrity, auditability, security, and regulatory defensibility**.

This document:
- records architectural intent,
- documents risks and mitigations,
- defines enforced guarantees,
- and establishes compliance-ready operational practices.

The database is treated as a **control surface**, not merely a persistence layer.

---

## 2. System Intent and Scope

The database acts as a canonical accounting abstraction layer between:
- external accounting providers,
- internal services and analytics,
- AI-assisted classification,
- downstream reporting and automation.

Key principles:
- UUID primary keys
- Provider IDs as references, not identities
- Organization-scoped ownership
- Append-first financial records
- Database-enforced correctness

---

## 3. Audit Findings Summary

Strengths:
- Strong normalization
- Clear domain modeling
- Migration discipline
- Audit and sync primitives

Risks addressed:
- Missing idempotency enforcement
- Weak domain constraints
- Excessive nullability
- Tenant isolation reliance on application code

All identified risks are mitigated by v2 schema hardening and governance controls defined herein.

---

## 4. v2 Schema Hardening (Implemented / Planned)

- Timestamp & boolean defaults
- CHECK constraints for currency and arithmetic
- Organization-scoped uniqueness
- Missing FK indexes
- updated_at enforcement triggers

Implemented via Alembic v2 migrations (Appendix C).

---

## 5. Operational Migration Checklist (DBA)

(unchanged from prior version)

---

## 6. FCA-Aligned Financial Governance

Mapped to FCA Principles:
- Principle 3 (Management & Control): enforced integrity
- Principle 11 (Relations with Regulators): traceability and audit logs
- Operational Resilience: idempotency and safe retries

---

## 7. Appendix A — Data Retention & Purge Policy

(unchanged, authoritative)

---

## 8. Appendix B — Row-Level Security & Tenant Isolation

(unchanged, authoritative)

---

## 9. Appendix C — Alembic v2 Migrations (Reference)

(unchanged, authoritative)

---

## 10. Appendix D — Data Classification & DPIA Alignment (SaaS Readiness)

### Purpose
Ensures the platform is compliant with UK GDPR obligations and SaaS best practices through explicit data classification and DPIA alignment.

### Data Classification Levels

| Classification | Examples | Controls |
|---------------|---------|----------|
| Public | Marketing metadata | No restrictions |
| Internal | Sync metadata | Access-controlled |
| Confidential | Financial transactions | Encryption, RLS |
| Restricted | OAuth tokens, PII | Encryption, minimal access |

### DPIA Mapping

Key DPIA considerations addressed by schema:
- Data minimization via retention policy
- Purpose limitation via table classification
- Access control via RLS
- Integrity via constraints and immutability
- Accountability via audit logs

The database design materially reduces DPIA risk and complexity.

---

## 11. Appendix E — Regulatory & Audit Evidence Pack Guidance

### Purpose
Defines how the database can produce evidence for:
- FCA inquiries
- Internal audits
- Customer assurance (SOC2-style)

### Evidence Sources

- Schema constraints (DDL)
- Migration history (Alembic)
- Audit tables
- Retention & purge logs
- RLS policies and role grants

### Recommended Evidence Pack Contents

- Current schema dump (schema-only)
- Migration history
- Role & privilege listings
- Sample audit trails
- Retention job logs

These artifacts can be generated without exposing customer data.

---

## 12. SaaS-Grade Best Practices (Going Forward)

Non-negotiable principles:
1. Database enforces invariants
2. Tenant isolation is structural
3. Financial data is append-only
4. Retention is intentional
5. Access is least-privilege
6. Evidence is always reproducible

---

## 13. Final Handover Checklist

- [ ] Master document approved
- [ ] Alembic migrations applied or scheduled
- [ ] Retention jobs implemented
- [ ] RLS design reviewed
- [ ] DPIA reviewed with stakeholders
- [ ] Evidence pack generation tested
- [ ] Document stored with schema and migrations

---

## 14. Final Statement

This database is **SaaS-ready by design**.

It encodes:
- correctness,
- security,
- auditability,
- and regulatory alignment

directly into its structure.

Future growth should refine these controls, not replace them.
