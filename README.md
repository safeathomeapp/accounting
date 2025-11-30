# 🚀 Accounting Platform - Master Development Guide

**IMPORTANT: This is the authoritative guide. Read this FIRST on every session.**

---

## ⚠️ NON-EDITABLE RULES FOR CLAUDE-CODE

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

---

## 📊 Current State (November 30, 2025)

### You Are Here: Month 6, Phase 3 - COMPLETE ✅
- **Backend**: ✅ Complete (Months 1-6) - 903/903 tests passing
- **Tests**: ✅ 903 passing (100%) - All verified
- **Frontend**: ✅ Phase 3 Complete - Full web interface ready
- **Next**: Phase 4 - Backend Integration & Real Database

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

### Phase 3 Frontend Features (Nov 24-30)
- ✅ **Week 1**: Error boundaries, toast notifications, skeleton loaders
- ✅ **Week 2**: Pagination, CSV export, date range filtering
- ✅ **Week 3**: Bulk operations (select, categorize, status, delete)
- ✅ **Final**: Dark mode theming, column sorting

---

## 🎯 Immediate Next Steps (Phase 4)

1. **Start Backend**
   ```bash
   cd C:/Users/kevth/desktop/projects/accountancy
   python -m uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
   ```

2. **Start Frontend**
   ```bash
   cd C:/Users/kevth/desktop/projects/accountancy/frontend
   npm run dev
   ```

3. **Phase 4 Planning**
   - [ ] Connect frontend to PostgreSQL backend
   - [ ] Real user authentication
   - [ ] Data persistence across sessions
   - [ ] Real-time sync monitoring
   - [ ] Multi-user support
   - [ ] Advanced analytics integration

---

## 🗺️ Development Roadmap

### Phase 3: Frontend Completion ✅ COMPLETE
**Goal**: Complete responsive web application
**Status**: 100% Complete (November 30, 2025)

#### Week 1 ✅
- ✅ Error boundaries & exception handling
- ✅ Toast notification system
- ✅ Skeleton loading placeholders
- ✅ Dashboard with dark mode toggle

#### Week 2 ✅
- ✅ Pagination component
- ✅ CSV export functionality
- ✅ Date range filtering
- ✅ Transaction list with filtering

#### Week 3 ✅
- ✅ Bulk selection system
- ✅ Bulk categorization
- ✅ Bulk status changes
- ✅ Bulk delete with confirmation

#### Final Polish ✅
- ✅ Dark mode theming system (localStorage persistence)
- ✅ Column sorting (strings, numbers, dates)
- ✅ Full responsive design verified
- ✅ All features documented

**Deliverables**: 11 reusable components, 4 custom hooks, 3 Zustand stores, 0 extra dependencies, 903/903 tests passing

### Phase 4: Backend Integration (Current - 2 weeks)
**Goal**: Production-ready system

#### Week 3
- User authentication (real users, not demo)
- Role-based access control
- Audit logging
- Performance optimization

#### Week 4
- Deployment setup (CI/CD)
- Documentation for end users
- Beta client onboarding process
- Monitoring and alerting setup

### Phase 5: Beta Launch (Month 7)
- Onboard 2-3 beta clients
- Daily monitoring and support
- Gather feedback and iterate
- Fix any critical issues

### Phase 6: Scale (Month 8+)
- Marketing website
- Automated onboarding
- Tiered pricing implementation
- Advanced features from FUTURE_FEATURES.md

---

## 🏗️ Architecture Guidelines

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

### Frontend Structure (IN PROGRESS)
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

---

## 📋 Development Checklist

### Before Starting Any Task
- [ ] Read this README.md
- [ ] Check current test count (must stay 903+)
- [ ] Review ARCHITECTURE_PRINCIPLES.md
- [ ] Understand the task completely (ask if <95% sure)

### During Development
- [ ] Write tests first (TDD)
- [ ] Follow existing patterns
- [ ] Document changes immediately
- [ ] Commit frequently with clear messages

### Before Ending Session
- [ ] All tests passing
- [ ] Documentation updated
- [ ] Create SESSION_NOTES_YYYY-MM-DD.md
- [ ] Commit all changes
- [ ] Note what's next

---

## 🚨 Critical Warnings

### DO NOT
- ❌ Refactor the backend without permission
- ❌ Break platform independence
- ❌ Skip writing tests
- ❌ Add features not in roadmap without discussion
- ❌ Change database schema without migration

### DO
- ✅ Add new features using existing patterns
- ✅ Maintain 95%+ test coverage
- ✅ Ask questions when uncertain
- ✅ Document everything
- ✅ Follow the roadmap

---

## 📚 Essential References

1. **Architecture**: `/ARCHITECTURE_PRINCIPLES.md`
2. **Future Features**: `/FUTURE_FEATURES.md`
3. **Original Roadmap**: `/DEFINITIVE_ROADMAP_V2.md`
4. **API Endpoints**: See `/backend/api/` directory
5. **Database Schema**: `/backend/models/`

---

## 🎯 Success Metrics

### Technical
- [ ] 95%+ test coverage maintained
- [ ] All platform adapters working
- [ ] <2 second page load times
- [ ] Zero security vulnerabilities

### Business
- [ ] Beta ready by Month 7
- [ ] 3 clients onboarded by Month 8
- [ ] Positive user feedback
- [ ] Stable, bug-free operation

---

## 📝 Session Notes Template

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
```

---

## 🔧 Quick Commands

```bash
# Backend
cd backend && uvicorn main:app --reload

# Frontend
cd frontend && npm run dev

# Tests
pytest tests/ -v

# Specific test file
pytest tests/test_[module].py -v

# With coverage
pytest tests/ --cov=backend --cov-report=html
```

---

## ✅ Remember

1. **The backend is production-ready** - Don't fix what isn't broken
2. **Platform abstraction is perfect** - Maintain it
3. **You're at Month 6** - Close to launch
4. **Focus on frontend** - That's the current priority
5. **Document everything** - Future you will thank you

---

**Last Updated**: November 30, 2025 (Phase 3 Complete)
**Next Review**: Before Phase 4 Backend Integration