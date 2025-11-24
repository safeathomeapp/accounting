# PROJECT INITIALIZATION FILE
# Multi-Platform AI Practice Management System
# Read this file FIRST before any code generation

---

## 🎯 PROJECT IDENTITY

**Project Name:** Multi-Platform AI Practice Management System  
**Code Name:** "Sage" (ironically, since we support multiple platforms including eventually Sage)  
**Version:** 2.0.0-alpha  
**Status:** Foundation Phase - Month 1  
**Start Date:** November 23, 2025  
**Target Completion:** November 2026 (12 months)

**Mission Statement:**
Build a professional-grade, AI-powered practice management system that works seamlessly with multiple accounting platforms (Xero, QuickBooks, and future additions), enabling bookkeepers to deliver superior service while mastering multiple platforms simultaneously.

---

## 👤 PROJECT LEAD

**Name:** [User]  
**Role:** Developer & Future Practice Owner  
**Experience Level:** Intermediate programmer with accounting knowledge  
**Current Status:** Studying accounting, launching practice in 12 months  
**Weekly Commitment:** 20 hours  
**Working Environment:** Windows 11, GitBash, PostgreSQL  
**Editor:** [To be confirmed]

---

## 🏗️ ARCHITECTURE OVERVIEW

### Core Philosophy: "Write Once, Run Anywhere"

This system uses the **Adapter Pattern** to achieve platform independence:

```
┌─────────────────────────────────────────┐
│  Business Logic Layer (Platform Agnostic)│
│  - AI Analysis                           │
│  - Client Communication                  │
│  - Reporting & Insights                  │
├─────────────────────────────────────────┤
│  Abstraction Layer (Standard Interface)  │
│  - AccountingClient (ABC)                │
│  - Standard Data Models                  │
│  - Factory Pattern                       │
├─────────────────────────────────────────┤
│  Platform Adapters (Specific Implementations)│
│  - XeroClient                            │
│  - QuickBooksClient                      │
│  - [Future: SageClient, FreeAgentClient] │
└─────────────────────────────────────────┘
```

**CRITICAL RULE:** Business logic must NEVER contain platform-specific code.

---

## 💻 TECHNICAL STACK

### Backend
- **Language:** Python 3.11+
- **Framework:** FastAPI
- **Database:** PostgreSQL (user preference - production-ready from day one)
- **ORM:** SQLAlchemy
- **Migrations:** Alembic
- **Testing:** pytest

### APIs
- **Claude (Anthropic):** AI analysis and communication
- **Xero:** Primary accounting platform (70% UK market)
- **QuickBooks Online:** Secondary platform (25% UK market)

### Frontend (Phase 3+)
- **Initial:** Plain HTML + Tailwind CSS
- **Later:** Optional React upgrade

### DevOps
- **Version Control:** Git + GitHub
- **Local Development:** Windows 11
- **Deployment:** Local initially, optional cloud later

---

## 📁 PROJECT STRUCTURE

```
accountancy/
├── .git/
├── .env                          # API keys (NEVER commit)
├── .env.example                  # Template for API keys
├── .gitignore
├── README.md
├── requirements.txt
├── PROJECT_INIT.md              # This file
│
├── docs/                        # Comprehensive documentation
│   ├── MULTI_PLATFORM_ROADMAP.md
│   ├── VISION.md
│   ├── TECH_STACK.md
│   ├── PLATFORM_INTEGRATION_GUIDE.md
│   ├── API_COST_OPTIMIZATION.md
│   └── SETUP_GUIDE.md
│
├── backend/                     # Python backend
│   ├── __init__.py
│   ├── main.py                  # FastAPI application
│   ├── config.py                # Configuration management
│   ├── database.py              # Database connection
│   │
│   ├── accounting/              # Platform abstraction layer
│   │   ├── __init__.py
│   │   ├── base.py              # Abstract AccountingClient
│   │   ├── models.py            # Standard data models
│   │   ├── factory.py           # Factory pattern
│   │   │
│   │   ├── xero/                # Xero adapter
│   │   │   ├── __init__.py
│   │   │   ├── client.py
│   │   │   ├── auth.py
│   │   │   └── mapper.py
│   │   │
│   │   └── quickbooks/          # QuickBooks adapter (Month 7+)
│   │       ├── __init__.py
│   │       ├── client.py
│   │       ├── auth.py
│   │       └── mapper.py
│   │
│   ├── ai/                      # AI integration (platform-agnostic)
│   │   ├── __init__.py
│   │   ├── analyzer.py          # Transaction analysis
│   │   ├── categorizer.py       # Categorization engine
│   │   ├── communicator.py      # Email generation
│   │   └── knowledge_base.py    # Knowledge base loader
│   │
│   ├── models/                  # Database models (SQLAlchemy)
│   │   ├── __init__.py
│   │   ├── client.py
│   │   ├── transaction.py
│   │   ├── task.py
│   │   └── insight.py
│   │
│   └── api/                     # API routes
│       ├── __init__.py
│       ├── routes.py
│       └── middleware.py
│
├── scripts/                     # Utility scripts
│   ├── sync_client.py           # Sync single client
│   ├── sync_all.py              # Sync all clients
│   ├── daily_review.py          # Daily analysis
│   └── test_*.py                # Test scripts
│
├── tests/                       # Test suite
│   ├── test_accounting/
│   ├── test_ai/
│   └── test_models/
│
├── alembic/                     # Database migrations
│   └── versions/
│
├── knowledge-base/              # AI knowledge base
│   ├── universal/               # Platform-agnostic rules
│   ├── xero-specific/
│   ├── quickbooks-specific/
│   └── platform-comparison.md
│
├── mock-clients/                # Mock client data
│   ├── xero/
│   │   ├── sarah-cafe/
│   │   ├── techfix-solutions/
│   │   └── buildright-construction/
│   └── quickbooks/
│       ├── shoplocal-online/
│       └── property-portfolio/
│
└── frontend/                    # Frontend (Phase 3+)
    ├── index.html
    ├── dashboard.html
    └── css/
```

---

## 📋 BEFORE GENERATING ANY CODE

**Claude Code MUST ask these questions:**

### 1. Context Questions
- [ ] What phase are we in? (Month 1-12)
- [ ] Which component are we working on?
- [ ] Is this new code or refactoring existing?
- [ ] Which platform(s) does this code touch?

### 2. Architecture Verification
- [ ] Does this code belong in business logic or adapter?
- [ ] Are we maintaining platform independence?
- [ ] Is this violating separation of concerns?
- [ ] Do we need to update tests?

### 3. Standards Compliance
- [ ] Have I read the relevant documentation first?
- [ ] Am I following the project's coding standards?
- [ ] Am I documenting as Steve Jobs would expect?
- [ ] Is this the simplest solution that works?

### 4. Integration Check
- [ ] What other components does this affect?
- [ ] Do I need to update the abstraction layer?
- [ ] Are there API cost implications?
- [ ] Does this require database migration?

**DO NOT write code until these are answered.**

---

## ⭐ THE STEVE JOBS STANDARD

### Design Philosophy

**"Simplicity is the ultimate sophistication."**

Every line of code must be:
1. **Necessary** - No code for "maybe later"
2. **Clear** - Any programmer understands it immediately
3. **Elegant** - The simplest solution possible
4. **Tested** - We know it works
5. **Documented** - Future us (and others) can maintain it

### Quality Standards

**Code Quality:**
- Type hints everywhere (Python 3.11+ style)
- Docstrings for every function, class, module
- No magic numbers (use constants)
- No god classes (single responsibility)
- DRY principle religiously followed

**Documentation Quality:**
- README for every major component
- Inline comments explain "why" not "what"
- Architecture decisions documented
- Examples for complex patterns
- Keep docs in sync with code

**User Experience (Even Internal Tools):**
- Clear error messages
- Helpful logging
- Intuitive naming
- Consistent patterns
- No surprises

**Testing Standard:**
- Test before committing
- Unit tests for business logic
- Integration tests for adapters
- Happy path AND edge cases
- Test coverage >80%

---

## 📝 DOCUMENTATION REQUIREMENTS

### Every File Must Have:

**Python Files:**
```python
"""
Module: [module name]
Purpose: [what this module does]
Dependencies: [key dependencies]
Platform: [universal | xero-specific | quickbooks-specific | platform-agnostic]

Example:
    from backend.accounting.xero.client import XeroClient
    
    client = XeroClient(credentials)
    transactions = client.get_transactions(start_date, end_date)

Author: [Name]
Created: [Date]
Last Modified: [Date]
"""
```

**Classes:**
```python
class ClassName:
    """
    One-line summary.
    
    Detailed explanation of what this class does,
    why it exists, and how to use it.
    
    Attributes:
        attr_name (type): Description
    
    Example:
        >>> obj = ClassName(param)
        >>> result = obj.method()
    """
```

**Functions:**
```python
def function_name(param: Type) -> ReturnType:
    """
    One-line summary of what function does.
    
    Detailed explanation if needed. Explain any non-obvious
    behavior, side effects, or important notes.
    
    Args:
        param: Description of parameter
    
    Returns:
        Description of return value
    
    Raises:
        ExceptionType: When this exception occurs
    
    Example:
        >>> result = function_name(value)
        >>> print(result)
    """
```

### Commit Messages:

**Format:**
```
[Type] Brief description (50 chars max)

Detailed explanation of:
- What changed
- Why it changed
- Any breaking changes
- Related issue numbers

Examples:
- Added Xero transaction normalization
- Fixed bug in date parsing for UK format
- Refactored abstraction layer for better separation
```

**Types:**
- `[FEAT]` - New feature
- `[FIX]` - Bug fix
- `[REFACTOR]` - Code refactoring
- `[DOCS]` - Documentation only
- `[TEST]` - Adding/updating tests
- `[CHORE]` - Maintenance tasks

---

## 🚨 CRITICAL RULES (NEVER VIOLATE)

### Rule 1: Platform Independence
```python
# ❌ WRONG - Xero code in business logic
def analyze_transactions():
    xero = Xero(credentials)
    txns = xero.banktransactions.all()

# ✅ CORRECT - Platform agnostic
def analyze_transactions(client):
    accounting = AccountingClientFactory.create(client)
    txns = accounting.get_transactions(start, end)
```

### Rule 2: Security
- **NEVER** commit API keys, credentials, or secrets
- **ALWAYS** use `.env` for sensitive data
- **ALWAYS** encrypt credentials in database
- **ALWAYS** use HTTPS in production

### Rule 3: Error Handling
```python
# ❌ WRONG - Silent failure
def get_data():
    return api.fetch()  # What if it fails?

# ✅ CORRECT - Explicit error handling
def get_data():
    try:
        return api.fetch()
    except APIError as e:
        logger.error(f"API fetch failed: {e}")
        raise DataFetchError(f"Could not fetch data: {e}")
```

### Rule 4: Type Safety
```python
# ❌ WRONG - No types
def process(data):
    return data['amount']

# ✅ CORRECT - Type hints
def process(data: Dict[str, Any]) -> Decimal:
    """Process transaction data."""
    if 'amount' not in data:
        raise ValueError("Missing amount in data")
    return Decimal(str(data['amount']))
```

### Rule 5: Testing
```python
# For every function, write a test
def test_process_transaction():
    """Test transaction processing with valid data."""
    data = {'amount': '100.50', 'date': '2025-01-01'}
    result = process(data)
    assert result == Decimal('100.50')

def test_process_transaction_missing_amount():
    """Test transaction processing with missing amount."""
    data = {'date': '2025-01-01'}
    with pytest.raises(ValueError):
        process(data)
```

---

## 💰 COST MANAGEMENT

### API Budget
- **Development (Month 1-12):** £20-30/month target
- **Claude API calls must be tracked**
- **Implement caching aggressively**
- **Use batch processing where possible**

### Before Calling Claude API, Ask:
1. Can this be solved with local rules? (FREE)
2. Can we batch this with other requests? (CHEAPER)
3. Can we cache the result? (SAVE MONEY)
4. Is this the minimal context needed? (REDUCE COST)

---

## 🔄 DEVELOPMENT WORKFLOW

### 1. Before Starting Feature
- [ ] Read relevant documentation
- [ ] Understand architecture implications
- [ ] Design solution (discuss with user if complex)
- [ ] Identify affected components
- [ ] Plan tests

### 2. During Development
- [ ] Write code following standards
- [ ] Add comprehensive docstrings
- [ ] Include inline comments for complex logic
- [ ] Think about error cases
- [ ] Consider API cost implications

### 3. After Writing Code
- [ ] Review for platform independence
- [ ] Write tests
- [ ] Update documentation if needed
- [ ] Check against style guide
- [ ] Add example usage

### 4. Before Committing
- [ ] Run tests
- [ ] Check no secrets in code
- [ ] Verify docstrings complete
- [ ] Write clear commit message
- [ ] Update CHANGELOG if significant

---

## 📊 CURRENT PROJECT STATUS

### Phase: Foundation (Month 1)
### Week: 1
### Current Sprint Goals:
1. Set up development environment
2. Create project structure
3. Establish API connections (Claude, Xero, QB)
4. Build abstraction layer foundation
5. Create first Xero adapter
6. Test with first mock client

### Completed:
- [ ] Project structure defined
- [ ] Documentation written
- [ ] Development environment set up
- [ ] API accounts created
- [ ] Git repository initialized

### In Progress:
- [ ] Abstraction layer implementation
- [ ] Xero adapter development
- [ ] Database schema creation

### Next Up:
- [ ] AI analysis engine
- [ ] Client data synchronization
- [ ] Basic dashboard

---

## 🎯 SUCCESS METRICS

### Code Quality Metrics:
- **Test Coverage:** Target >80%
- **Docstring Coverage:** Target 100%
- **Type Hint Coverage:** Target 100%
- **Linting:** No errors, minimal warnings
- **Complexity:** Max cyclomatic complexity 10

### Performance Metrics:
- **API Response Time:** <2s for standard operations
- **Database Queries:** Optimized (use EXPLAIN)
- **Memory Usage:** Monitor and optimize
- **API Costs:** Track per client, stay under budget

### Documentation Metrics:
- **Every module documented:** Yes/No
- **README up to date:** Yes/No
- **Architecture diagrams current:** Yes/No
- **Examples working:** Yes/No

---

## 🤝 COLLABORATION PROTOCOL

### When User Asks for Code:

**Step 1: Understand**
- Ask clarifying questions
- Confirm which phase/component
- Verify architectural implications

**Step 2: Design**
- Explain approach before coding
- Get user approval on design
- Discuss alternatives if complex

**Step 3: Implement**
- Write clean, documented code
- Follow all standards
- Include tests

**Step 4: Deliver**
- Explain what code does
- Show how to test it
- Document any gotchas

### When User Reports Bug:

**Step 1: Reproduce**
- Get exact steps to reproduce
- Understand expected vs actual behavior
- Check logs/error messages

**Step 2: Diagnose**
- Identify root cause
- Explain what went wrong
- Propose fix

**Step 3: Fix**
- Implement solution
- Add test to prevent regression
- Update documentation if needed

### When User Requests Feature:

**Step 1: Clarify**
- Understand the need
- Discuss architecture fit
- Estimate complexity

**Step 2: Design**
- Propose solution
- Discuss trade-offs
- Get approval

**Step 3: Implement**
- Follow standards
- Write tests
- Document thoroughly

---

## 📚 REQUIRED READING

Before touching any component, read:

**For Abstraction Layer:**
- `docs/PLATFORM_INTEGRATION_GUIDE.md`

**For Xero Integration:**
- `docs/TECH_STACK.md` (Xero section)
- `knowledge-base/xero-specific/` (all files)

**For QuickBooks Integration:**
- `docs/PLATFORM_INTEGRATION_GUIDE.md`
- `knowledge-base/quickbooks-specific/` (all files)

**For AI Integration:**
- `docs/API_COST_OPTIMIZATION.md`
- `knowledge-base/universal/` (categorization rules)

**For Database:**
- `backend/models/` (all model definitions)
- Database schema documentation

---

## 🔍 CODE REVIEW CHECKLIST

Before declaring code "done", verify:

**Architecture:**
- [ ] No platform-specific code in business logic?
- [ ] Follows adapter pattern correctly?
- [ ] Proper separation of concerns?
- [ ] Consistent with existing patterns?

**Code Quality:**
- [ ] Type hints on all functions?
- [ ] Docstrings complete and accurate?
- [ ] No magic numbers or strings?
- [ ] Error handling comprehensive?
- [ ] No code duplication?

**Testing:**
- [ ] Unit tests written?
- [ ] Tests actually pass?
- [ ] Edge cases covered?
- [ ] Happy path and error paths tested?

**Documentation:**
- [ ] Module docstring present?
- [ ] Function docstrings complete?
- [ ] Complex logic explained?
- [ ] Examples included where helpful?

**Security:**
- [ ] No secrets in code?
- [ ] Input validation present?
- [ ] SQL injection prevention?
- [ ] API keys secured?

**Performance:**
- [ ] API calls minimized?
- [ ] Database queries optimized?
- [ ] Caching implemented where appropriate?
- [ ] No obvious performance issues?

---

## 🎓 LEARNING OBJECTIVES

This project teaches:

**For User:**
- Xero proficiency
- QuickBooks proficiency
- Python/FastAPI development
- System architecture
- AI integration
- PostgreSQL database design

**For Future Team:**
- Clean architecture patterns
- Multi-platform integration
- AI-powered automation
- Professional development practices

**Documentation serves both purposes.**

---

## 🚀 GETTING STARTED

### First Time Setup:
1. Read this file completely
2. Review `docs/MULTI_PLATFORM_ROADMAP.md`
3. Check `docs/TECH_STACK.md`
4. Understand `docs/PLATFORM_INTEGRATION_GUIDE.md`
5. Ask user: "What are we building today?"

### Before Each Session:
1. Ask: "Where are we in the roadmap?"
2. Ask: "What's the goal for today?"
3. Review: What was completed last session
4. Confirm: Any blockers or issues

### After Each Session:
1. Summarize: What was accomplished
2. Update: Project status in this file
3. Document: Any decisions made
4. Plan: Next session's goals

---

## ✨ INSPIRATION

**"We're here to put a dent in the universe."** - Steve Jobs

This isn't just a practice management tool.
This is a system that will:
- Help small business owners succeed
- Make bookkeepers more efficient
- Demonstrate what's possible with AI
- Set a standard for quality
- Launch a successful practice

**Build it like it matters. Because it does.**

---

## 📞 FINAL NOTES

**Remember:**
- Quality over speed
- Simple over complex
- Documented over clever
- Tested over assumed
- Professional over "good enough"

**When in doubt:**
- Ask the user
- Check the documentation
- Follow the standards
- Test thoroughly

**This project will be shown to:**
- Future employers
- Potential clients
- Other developers
- The accounting community

**Make it something we're proud of.**

---

## 🔄 VERSION HISTORY

**v2.0.0 - November 22, 2025**
- Initial multi-platform version
- Established standards and workflow
- Ready for development

---

**Last Updated:** November 22, 2025  
**Next Review:** End of Month 1  
**Maintained By:** Project Lead + Claude Code

---

**END OF INITIALIZATION FILE**
