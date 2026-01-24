# Accounting Platform - Master Development Guide

**IMPORTANT: This is the authoritative guide. Read this FIRST on every session.**

---

## NON-EDITABLE RULES FOR CLAUDE-CODE

**These rules are MANDATORY and must be followed on every session:**

1. **Documentation Requirements**
   - Document ALL changes as you make them
   - Update relevant .md files immediately after significant changes
   - Create session notes at the END of EVERY session
   - Comment complex code sections inline
   - Keep test coverage above 95%

2. **Communication Protocol**
   - If <95% certain about a requirement: ASK FOR CLARIFICATION
   - Present options when multiple approaches exist
   - Confirm before making breaking changes
   - Explain technical decisions clearly

3. **Code Quality Standards**
   - Follow ARCHITECTURE_PRINCIPLES.md strictly
   - Maintain platform independence (already excellent)
   - Write tests BEFORE implementation (TDD)
   - No code without tests
   - Follow Python PEP 8 and JavaScript best practices

4. **Session Management**
   - Start: Read this README.md
   - During: Document changes in real-time
   - End: Create SESSION_NOTES_YYYY-MM-DD.md
   - Include: What was done, what's next, any blockers

5. **Backend Preservation**
   - The backend is PRODUCTION-READY - don't refactor without explicit permission
   - ADD new functionality, don't REPLACE existing
   - Platform abstraction is PERFECT - maintain it
   - 903 tests must continue passing

6. **Database Changes**
   - ALL schema changes MUST go through Alembic migrations
   - Run pre-flight validation queries before applying migrations
   - Document every migration with clear upgrade/downgrade paths
   - Never modify production data without explicit permission

---

## Current State (January 24, 2026)

### You Are Here: Month 6, Phase 3 Complete - Preparing for Phase 4

| Component | Status | Notes |
|-----------|--------|-------|
| Backend | ✅ Complete | 903/903 tests passing |
| Frontend | ✅ Phase 3 Complete | Full web interface ready |
| Database Schema | ⚠️ Hardening Required | See Phase 4A below |
| Platform Adapters | ✅ Xero + QuickBooks | FreeAgent docs ready |
| Dark Mode | ✅ Fixed | Verified Jan 22, 2026 |
| Mock Data | ✅ Expanded | 25 transactions for testing |

### Completed Features
- ✅ Multi-platform sync (Xero + QuickBooks)
- ✅ Advanced analytics & forecasting
- ✅ Tax compliance system
- ✅ Multi-currency support
- ✅ Report generation (PDF/Excel/CSV)
- ✅ Mobile API with JWT auth
- ✅ Background job scheduling
- ✅ Real-time monitoring
- ✅ Web Frontend (React + Vite + TailwindCSS)
- ✅ User authentication flow (JWT)
- ✅ Dashboard with dark mode
- ✅ Transaction management (list, sort, filter, bulk ops)
- ✅ Account/Sync monitoring pages
- ✅ Error handling & notifications
- ✅ Pagination & data export (CSV)
- ✅ Responsive design (mobile-ready)

### In Progress
- 📝 FreeAgent platform documentation (API Guide + Blueprint complete)
- ⏳ Awaiting FreeAgent sandbox API access
- 📋 Database hardening planning (this document)

---

## Development Roadmap

### Phase 3: Frontend Completion ✅ COMPLETE
**Status**: 100% Complete (November 30, 2025)

- ✅ Error boundaries & exception handling
- ✅ Toast notification system
- ✅ Skeleton loading placeholders
- ✅ Dashboard with dark mode toggle
- ✅ Pagination component
- ✅ CSV export functionality
- ✅ Date range filtering
- ✅ Bulk operations (select, categorize, status, delete)
- ✅ Column sorting (strings, numbers, dates)

**Deliverables**: 11 reusable components, 4 custom hooks, 3 Zustand stores

---

### Phase 4A: Database Hardening ⚠️ CRITICAL - DO FIRST
**Goal**: Production-ready database before connecting frontend
**Status**: Planned
**Priority**: MANDATORY before Phase 4B

#### Why This Is Required
An external team audited the database architecture and identified critical issues that MUST be resolved before production use. Full documentation is in `/docs/DATABASE_ARCHITECTURE/`.

#### Critical Migrations (MANDATORY)

| Migration | Priority | Description | Risk if Skipped |
|-----------|----------|-------------|-----------------|
| v2_040 | **CRITICAL** | Organization-scoped uniqueness | Multi-tenancy broken - two orgs cannot sync same invoice ID |
| v2_020 | **HIGH** | Currency/amount CHECK constraints | Invalid financial data can be stored permanently |

#### Recommended Migrations

| Migration | Priority | Description | Benefit |
|-----------|----------|-------------|---------|
| v2_010 | MEDIUM | Defaults and updated_at triggers | Guaranteed timestamp consistency |
| v2_030 | LOW | Missing FK indexes | Query performance improvement |
| v2_001 | LOW | pgcrypto extension | Optional DB-side UUID generation |

#### Phase 4A Checklist

**Pre-Flight Validation (Run First):**
```sql
-- Check for duplicate platform references (MUST return 0 rows)
SELECT organization_id, platform_name, platform_id, COUNT(*)
FROM clients
GROUP BY 1,2,3
HAVING COUNT(*) > 1;

SELECT organization_id, platform_name, platform_id, COUNT(*)
FROM transactions
GROUP BY 1,2,3
HAVING COUNT(*) > 1;

-- Check arithmetic consistency (MUST return 0 rows)
SELECT id, amount, tax_amount, total_amount
FROM transactions
WHERE total_amount != amount + tax_amount;
```

**Implementation Order:**
- [ ] Run pre-flight validation queries
- [ ] Fix any data issues found
- [ ] Apply v2_040 (org-scoped uniqueness) - CRITICAL
- [ ] Apply v2_020 (currency/amount checks) - HIGH
- [ ] Apply v2_010 (defaults/triggers) - MEDIUM
- [ ] Apply v2_030 (FK indexes) - LOW
- [ ] Verify all 903 tests still pass
- [ ] Document completion in session notes

**Time Estimate**: 2-3 hours

**Reference Documentation**:
- `/docs/DATABASE_ARCHITECTURE/MASTER_DATABASE_COMPENDIUM.md` - Full technical details
- `/docs/DATABASE_ARCHITECTURE/MASTER_GOVERNANCE_DOCUMENT.md` - Governance & compliance
- `/docs/DATABASE_ARCHITECTURE/current_schema_export_2026-01-22.sql` - Current schema snapshot

---

### Phase 4B: Platform Expansion
**Goal**: Add FreeAgent, ClearBooks, FreshBooks adapters
**Status**: FreeAgent documentation complete, awaiting API access

#### Platform Integration Status

| Platform | Documentation | API Access | Implementation |
|----------|--------------|------------|----------------|
| Xero | ✅ Complete | ✅ Available | ✅ Complete |
| QuickBooks | ✅ Complete | ✅ Available | ✅ Complete |
| FreeAgent | ✅ Complete | ⏳ Pending sandbox | ⏳ Pending |
| ClearBooks | ⏳ Pending | ⏳ Pending | ⏳ Pending |
| FreshBooks | ⏳ Pending | ⏳ Pending | ⏳ Pending |
| Sage Cloud | 📋 Planned | ⏳ Pending | ⏳ Pending |

#### FreeAgent Status
- ✅ API Guide created: `/docs/PLATFORM_GUIDES/FREEAGENT_API_GUIDE.md`
- ✅ Implementation Blueprint: `/docs/PLATFORM_GUIDES/FREEAGENT_IMPLEMENTATION_BLUEPRINT.md`
- ✅ Data Mapping Spec updated with FreeAgent section
- ⏳ Email sent to FreeAgent integrations team for Practice API sandbox access
- ⏳ Awaiting response before implementation can begin

#### Phase 4B Checklist (Per Platform)
- [ ] Research API documentation
- [ ] Create API Guide (authentication, endpoints, quirks)
- [ ] Create Implementation Blueprint (code walkthrough)
- [ ] Update Data Mapping Spec
- [ ] Obtain API credentials/sandbox access
- [ ] Implement platform adapter
- [ ] Write comprehensive tests (80%+ coverage)
- [ ] Integration testing with sandbox
- [ ] Document completion

---

### Phase 4C: Backend Integration
**Goal**: Connect frontend to real PostgreSQL database
**Status**: Pending (after 4A and 4B)

#### Checklist
- [ ] Database hardening complete (Phase 4A)
- [ ] At least one new platform adapter complete (Phase 4B)
- [ ] Connect frontend to PostgreSQL backend
- [ ] Real user authentication (not demo)
- [ ] Data persistence across sessions
- [ ] Real-time sync monitoring
- [ ] Role-based access control
- [ ] Audit logging verification
- [ ] Performance optimization

---

### Phase 5: Production Hardening (Month 7)
**Goal**: Security and compliance readiness

#### Row-Level Security (RLS)
- [ ] Create database roles (app_user, app_readonly, app_admin)
- [ ] Enable RLS on tenant-scoped tables
- [ ] Modify FastAPI to set session context
- [ ] Test tenant isolation thoroughly

#### Data Retention Implementation
- [ ] Implement purge procedures for operational data
- [ ] Set up scheduled jobs (pg_cron or application-level)
- [ ] Log all purge operations to audit_log
- [ ] Verify 7-year retention for financial data

#### Evidence Pack
- [ ] Store audit scripts in repository
- [ ] Document evidence generation process
- [ ] Create baseline evidence pack
- [ ] Test regulatory inquiry response process

---

### Phase 6: Beta Launch (Month 7-8)
- [ ] Onboard 2-3 beta clients
- [ ] Daily monitoring and support
- [ ] Gather feedback and iterate
- [ ] Fix any critical issues

### Phase 7: Scale (Month 8+)
- [ ] Marketing website
- [ ] Automated onboarding
- [ ] Tiered pricing implementation
- [ ] Advanced features from FUTURE_FEATURES.md

---

## Quick Start Commands

```bash
# Backend
cd C:/Users/kevth/desktop/projects/accountancy
python -m uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000

# Frontend
cd C:/Users/kevth/desktop/projects/accountancy/frontend
npm run dev

# Tests
pytest tests/ -v

# Tests with coverage
pytest tests/ --cov=backend --cov-report=html
```

---

## Architecture Guidelines

### Backend Structure (DO NOT CHANGE)
```
backend/
├── accounting/      # Platform adapters ✅ PERFECT
├── ai/             # AI integration (empty - future)
├── analytics/      # Analytics engine ✅ COMPLETE
├── api/            # REST endpoints ✅ COMPLETE
├── currency/       # Multi-currency ✅ COMPLETE
├── models/         # Database models ✅ COMPLETE
├── monitoring/     # Real-time monitoring ✅ COMPLETE
├── reporting/      # Report generation ✅ COMPLETE
├── sync/           # Sync engine ✅ COMPLETE
└── tax/            # Tax compliance ✅ COMPLETE
```

### Frontend Structure
```
frontend/
├── src/
│   ├── pages/      # Page components
│   ├── components/ # Reusable components
│   ├── services/   # API client
│   ├── stores/     # State management
│   └── utils/      # Helper functions
```

### Key Principles
1. **Platform Independence**: Maintained through factory pattern
2. **Separation of Concerns**: Each module has single responsibility
3. **Configuration Over Code**: Use database for feature flags
4. **Test Everything**: Minimum 95% coverage
5. **Document As You Go**: Every feature needs docs
6. **Database Enforces Correctness**: Constraints at DB level, not just application

---

## Essential References

### Architecture & Design
| Document | Location | Purpose |
|----------|----------|---------|
| Architecture Principles | `/docs/architecture/ARCHITECTURE_PRINCIPLES.md` | Core design principles |
| Abstraction Layer | `/docs/architecture/abstraction_layer.md` | Platform adapter design |
| Future Features | `/FUTURE_FEATURES.md` | Planned enhancements |

### Database
| Document | Location | Purpose |
|----------|----------|---------|
| **Master Compendium** | `/docs/DATABASE_ARCHITECTURE/MASTER_DATABASE_COMPENDIUM.md` | Full technical reference including migrations |
| **Governance Document** | `/docs/DATABASE_ARCHITECTURE/MASTER_GOVERNANCE_DOCUMENT.md` | FCA alignment, compliance, policies |
| Current Schema | `/docs/DATABASE_ARCHITECTURE/current_schema_export_2026-01-22.sql` | PostgreSQL schema snapshot |
| Evidence Scripts | `/docs/DATABASE_ARCHITECTURE/evidence_pack_scripts/` | Audit artifact generation |

### Platform Guides
| Document | Location | Purpose |
|----------|----------|---------|
| Xero API Guide | `/docs/PLATFORM_GUIDES/XERO_API_GUIDE.md` | Xero integration reference |
| QuickBooks API Guide | `/docs/PLATFORM_GUIDES/QUICKBOOKS_API_GUIDE.md` | QuickBooks integration reference |
| FreeAgent API Guide | `/docs/PLATFORM_GUIDES/FREEAGENT_API_GUIDE.md` | FreeAgent integration reference |
| Data Mapping Spec | `/docs/PLATFORM_GUIDES/DATA_MAPPING_SPEC.md` | Field mappings for all platforms |

### Session History
| Document | Location | Purpose |
|----------|----------|---------|
| Session Notes | `/docs/SESSION_NOTES/` | Daily development logs |
| Session Starter | `/SESSION_STARTER_2025-12-01.md` | Quick context recovery |

---

## Critical Warnings

### DO NOT
- ❌ Refactor the backend without permission
- ❌ Break platform independence
- ❌ Skip writing tests
- ❌ Add features not in roadmap without discussion
- ❌ Change database schema without Alembic migration
- ❌ Apply database migrations without pre-flight validation
- ❌ Remove existing documentation

### DO
- ✅ Add new features using existing patterns
- ✅ Maintain 95%+ test coverage
- ✅ Ask questions when uncertain
- ✅ Document everything
- ✅ Follow the roadmap
- ✅ Run pre-flight checks before database changes
- ✅ Keep session notes comprehensive

---

## Success Metrics

### Technical
- [ ] 95%+ test coverage maintained
- [ ] All 6 platform adapters working (Xero, QB, FreeAgent, ClearBooks, FreshBooks, Sage)
- [ ] <2 second page load times
- [ ] Zero security vulnerabilities
- [ ] Database constraints enforce all invariants
- [ ] Row-level security active in production

### Business
- [ ] Beta ready by Month 7
- [ ] 3 clients onboarded by Month 8
- [ ] Positive user feedback
- [ ] Stable, bug-free operation
- [ ] FCA-aligned data governance

---

## Session Notes Template

When ending a session, create:
`/docs/SESSION_NOTES/SESSION_NOTES_YYYY-MM-DD.md`

```markdown
# Session Notes - [Date]

## Completed
- [List what was done]

## In Progress
- [List partial work]

## Blockers
- [List any issues]

## Next Session
- [List priorities]

## Notes
- [Any important context]

## Files Modified
- [List files changed with brief description]
```

---

## Remember

1. **The backend is production-ready** - Don't fix what isn't broken
2. **Platform abstraction is perfect** - Maintain it
3. **Database hardening is MANDATORY** - Complete Phase 4A first
4. **You're at Month 6** - Close to launch
5. **Documentation is paramount** - Future you will thank you
6. **6 platforms total** - Xero, QuickBooks, FreeAgent, ClearBooks, FreshBooks, Sage

---

**Last Updated**: January 24, 2026
**Updated By**: Claude Code session - Database hardening integration
**Next Priority**: Phase 4A - Database Hardening (CRITICAL)
