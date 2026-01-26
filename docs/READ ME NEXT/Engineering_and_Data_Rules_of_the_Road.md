# Engineering & Data Rules of the Road
## Multi‑Platform Accounting Ingestion, Reporting, and AI (v1 → vN)

Date: 2026‑01‑26  
Audience: Engineering, Data, Product, Security  
Purpose: Provide long‑lived rules, constraints, and decision paths to keep the system correct, scalable, and defensible as scope and platforms expand.

---

## 1. Non‑Negotiable Architectural Principles

These are not guidelines. They are constraints.

### 1.1 The Three‑Layer Rule
All data must flow through these layers in order:

**Raw → Mapping → Canonical Facts → Reports / AI**

- Raw data is never trusted.
- Mapping defines meaning.
- Canonical facts are the only truth.
- Reports and AI must *never* read raw tables.

If a feature cannot respect this flow, it does not ship.

---

### 1.2 Database Is the Contract
The database enforces meaning, not application code.

- Enums > free text
- CHECK constraints > comments
- Derived facts tables > “smart queries”
- RLS > relying on developers to remember WHERE clauses

Assume application bugs will happen. Design so they cannot leak data or semantics.

---

### 1.3 Default‑Deny Data Philosophy
If data cannot be confidently interpreted:
- It is excluded from facts
- It is quarantined
- It is surfaced as a data‑quality issue

Silent assumptions are forbidden.

---

## 2. Rules for Ingestion & Platform Expansion

### 2.1 Never Hard‑Code Platform Meaning
No connector may:
- infer direction from sign alone
- assume status semantics
- embed “if platform == X” logic in reporting paths

All platform differences must be expressed in:
- `platform_transaction_mapping`

This is what makes adding a new platform a data exercise, not a refactor.

---

### 2.2 Platform Onboarding Checklist (Mandatory)
Before enabling reports for a new platform:
1. Raw ingestion working and audited
2. Mapping rows exist for all observed source types/statuses
3. Mapping coverage ≥ 95%
4. Zero UNKNOWN mappings in reportable date range
5. Facts table rebuild produces no quarantine events

If any step fails, reporting stays disabled for that platform.

---

## 3. Rules for Reporting

### 3.1 Reports Read Facts Only
Reports:
- MUST read from canonical facts tables
- MUST NOT join directly to raw transactions
- MUST NOT contain platform‑specific logic

If a report “needs” raw data, the facts layer is incomplete.

---

### 3.2 Reports Are Deterministic
Given the same facts:
- The report output must be identical
- Forecasts must be reproducible
- AI explanations must be traceable

No randomness without an explicit seed and provenance record.

---

### 3.3 Reports Must Declare Assumptions
Every report must expose:
- What data is included
- What is excluded
- What assumptions are applied (e.g. “paid assumed cash moved”)

If it cannot be explained to an accountant, it is not ready.

---

## 4. Rules for AI Integration (When It Comes)

### 4.1 AI Never Touches Raw Data
AI agents may only access:
- Canonical facts
- Explicit aggregates
- Provenance metadata

AI must not:
- infer semantics
- “fix” missing data
- override mapping decisions

AI is an interpreter, not an arbiter.

---

### 4.2 AI Outputs Are Suggestions, Not Truth
AI outputs must:
- be stored separately from facts
- reference the facts used
- be reproducible
- be explainable in plain English

AI does not mutate financial truth.

---

## 5. Data Quality & Operational Rules

### 5.1 Quarantine Is a Feature, Not a Failure
Quarantine events mean:
- the system is working
- drift was detected
- reports were protected

Never “quick‑fix” quarantine by loosening constraints.

---

### 5.2 Data Quality Metrics Are First‑Class
Track and review:
- mapping coverage %
- quarantine event count
- missing due dates
- unknown status/type frequency

These metrics should be visible internally at all times.

---

## 6. Security & Multi‑Tenant Rules

### 6.1 Tenant Context Is Mandatory
- Tenant context must be set at connection/session start
- RLS must enforce tenant isolation in the DB
- APIs must not trust tenant IDs from clients

Assume every endpoint will eventually be misused.

---

### 6.2 Private Data Is Never Cacheable
All report responses must include:
- `Cache‑Control: no‑store`
- No CDN caching
- No static file serving of private content

Reports are documents, not web assets.

---

## 7. Change Management Rules

### 7.1 Schema Changes
Any change that affects:
- mapping
- facts
- reporting semantics

Requires:
- migration
- backfill plan
- rollback plan
- updated documentation

“No‑migration fixes” are forbidden in these areas.

---

### 7.2 Feature Sequencing Rule
New features must follow this order:
1. Raw data available
2. Mapping defined
3. Facts generated
4. Constraints enforced
5. Report built
6. AI layered (optional)

Skipping steps creates technical debt that accountants will find.

---

## 8. Product & Design Guidance

### 8.1 Fewer Reports, Better Explained
It is better to ship:
- one report clients trust
than:
- five reports clients export to Excel “just to check”

Clarity beats breadth.

---

### 8.2 Always Show “As Of”
Every report must show:
- data as‑of timestamp
- last sync timestamp (per platform/client)

Without this, users will assume the worst.

---

## 9. What Success Looks Like

You will know the system is working when:
- Adding a new platform means adding mapping rows, not code paths
- A data anomaly results in quarantine, not a silent chart change
- Two engineers independently generate the same report from the same facts
- An accountant asks “why?” and the system can answer

---

## 10. Final Direction to the Team

You are not building:
- dashboards
- charts
- AI magic

You are building:
> **A system that accountants can trust without spreadsheets.**

Every decision should be judged against that bar.

