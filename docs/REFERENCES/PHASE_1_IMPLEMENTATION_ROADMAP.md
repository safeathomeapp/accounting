# Phase 1 Implementation Roadmap
**Foundation Phase: Months 1-2**
**Current Status:** Week 1 Complete - Ready for Week 2
**Date Created:** November 23, 2025

---

## 🗺️ PHASE 1 OVERVIEW

### Phase 1 Goals
```
Week 1:   ✅ DONE - Environment setup + project structure
Week 2-3: Database + Models + API foundation
Week 4-5: Abstraction layer + Xero adapter
Week 6-8: Testing + polish + documentation
```

### What Phase 1 Delivers
- Working FastAPI application
- PostgreSQL database with migrations
- Platform-independent abstraction layer
- Functional Xero integration
- Ability to fetch data from Xero
- Comprehensive test coverage
- Production-ready foundation

---

## 📋 NEXT TASKS (Prioritized)

### Task 1: Initialize Alembic & Database Migrations
**Priority:** CRITICAL - Must do first
**Time Estimate:** 45 minutes
**Status:** Ready to start immediately

**What This Does:**
- Sets up database versioning system
- Creates migration tracking table
- Enables safe database schema updates
- Creates version history in git

**Steps:**
```bash
1. cd C:\Users\kevth\Desktop\Projects\Accountancy
2. source venv/Scripts/activate
3. alembic init alembic (DONE - directory exists)
4. Edit alembic.ini to point to DATABASE_URL
5. Create env.py for auto-migrations
6. Run: alembic revision --autogenerate -m "initial_schema"
7. Run: alembic upgrade head
```

**Deliverables:**
- `alembic/` folder configured
- `alembic/versions/001_initial_schema.py` migration file
- Database schema created in PostgreSQL

**Success Criteria:**
- Migration file created without errors
- `alembic upgrade head` runs successfully
- 9 tables exist in accountancy_dev database
- Can query tables with psql

---

### Task 2: Create SQLAlchemy Database Models
**Priority:** CRITICAL - Depends on Task 1
**Time Estimate:** 1.5 hours
**Status:** Schema already designed, ready to code

**What This Does:**
- Defines Python classes for database tables
- Provides type-safe database access
- Creates ORM relationships
- Enables validation and serialization

**Files to Create:**
```
backend/models/
├── __init__.py                  # Import all models
├── organization.py              # Organization model
├── accounting_platform.py        # Platform credentials
├── client.py                    # Customers/contacts
├── transaction.py               # Financial transactions
├── account.py                   # Chart of accounts
├── oauth_token.py               # OAuth token storage
├── ai_analysis.py               # AI analysis results
├── sync_history.py              # Sync tracking
└── audit_log.py                 # Audit trail
```

**Steps:**
```bash
1. Create each model file
2. Define SQLAlchemy classes
3. Add relationships between models
4. Add validators using Pydantic
5. Create conftest.py for tests
6. Run tests to verify models work
```

**Deliverables:**
- 9 SQLAlchemy model classes
- All relationships defined
- Type hints throughout
- Ready for API routes

**Success Criteria:**
- Models import without errors
- Can create instances in Python
- Relationships work correctly
- Type hints are accurate

---

### Task 3: Set Up FastAPI Application Structure
**Priority:** HIGH - Core API infrastructure
**Time Estimate:** 1 hour
**Status:** Ready to build

**What This Does:**
- Creates main FastAPI application
- Sets up middleware (logging, error handling)
- Creates API route structure
- Configures CORS for frontend

**Files to Create:**
```
backend/
├── main.py                      # FastAPI app entry point
├── config.py                    # Configuration management
└── database.py                  # Database connection utilities
```

**backend/main.py will include:**
```python
- FastAPI app initialization
- Middleware setup
- CORS configuration
- Database session management
- Root route (GET /)
- Health check route (GET /health)
- API v1 routes structure (GET /api/v1/...)
- Error handlers
- Logging setup
```

**Steps:**
```bash
1. Create config.py with environment variables
2. Create database.py with session management
3. Create main.py with FastAPI app
4. Add middleware for logging
5. Add CORS configuration
6. Create basic health check route
7. Test: uvicorn backend.main:app --reload
```

**Deliverables:**
- Working FastAPI application
- Can run with `uvicorn backend.main:app --reload`
- Health check endpoint working
- Database connection verified

**Success Criteria:**
- Server starts without errors
- GET /health returns 200 OK
- Swagger documentation at /docs
- Database session working

---

### Task 4: Build Abstraction Layer (AccountingClient)
**Priority:** CRITICAL - Foundation for all integrations
**Time Estimate:** 2 hours
**Status:** Fully designed, ready to code

**What This Does:**
- Creates platform-independent interface
- Defines what all adapters must implement
- Ensures consistent behavior across platforms
- Makes code platform-agnostic

**Files to Create:**
```
backend/accounting/
├── __init__.py
├── base.py                      # Abstract base class
├── models.py                     # Standard data models
├── factory.py                    # Factory pattern
└── exceptions.py                # Custom exceptions
```

**Key Classes:**

1. **base.py - AccountingClient (Abstract Base Class)**
```python
class AccountingClient(ABC):
    """Abstract base for all accounting platform clients"""

    @abstractmethod
    async def authenticate(self) -> bool

    @abstractmethod
    async def get_contacts(self, updated_since: datetime) -> List[Contact]

    @abstractmethod
    async def get_transactions(self, start_date: date, end_date: date) -> List[Transaction]

    @abstractmethod
    async def get_accounts(self) -> List[Account]

    @abstractmethod
    async def create_invoice(self, invoice_data: dict) -> dict

    # ... etc for all operations
```

2. **models.py - Standard Data Models**
```python
class Contact(BaseModel):
    """Platform-independent contact representation"""
    id: str
    name: str
    email: Optional[str]
    # ... standardized fields only

class Transaction(BaseModel):
    """Platform-independent transaction representation"""
    id: str
    date: date
    amount: Decimal
    # ... standardized fields only

# etc for all data types
```

3. **factory.py - Client Factory**
```python
class AccountingClientFactory:
    @staticmethod
    def create(platform_name: str, credentials: dict) -> AccountingClient:
        if platform_name == 'xero':
            return XeroClient(credentials)
        elif platform_name == 'quickbooks':
            return QuickBooksClient(credentials)
        else:
            raise ValueError(f"Unknown platform: {platform_name}")
```

**Steps:**
```bash
1. Create base.py with abstract class
2. Define all required methods
3. Create models.py with standard models
4. Create factory.py with factory pattern
5. Create exceptions.py with custom exceptions
6. Write tests for factory
7. Verify no platform-specific code in base
```

**Deliverables:**
- Abstract AccountingClient class
- 4-5 standard data models
- Factory pattern implementation
- Custom exception classes

**Success Criteria:**
- Can't instantiate abstract class (correct)
- Factory creates correct client type
- All models validate correctly
- No platform-specific code in base

---

### Task 5: Develop Xero Adapter
**Priority:** HIGH - First working integration
**Time Estimate:** 2-3 hours
**Status:** SDK ready, ready to implement

**What This Does:**
- Connects to Xero API
- Implements AccountingClient interface
- Normalizes Xero data to standard format
- Handles OAuth2 authentication

**Files to Create:**
```
backend/accounting/xero/
├── __init__.py
├── client.py                    # Main Xero client
├── auth.py                      # OAuth2 handling
└── mapper.py                    # Data normalization
```

**Structure:**

1. **client.py - XeroClient Class**
```python
class XeroClient(AccountingClient):
    """Xero-specific implementation of AccountingClient"""

    def __init__(self, org: Organization):
        self.org = org
        self.platform = org.accounting_platforms[0]  # Xero platform
        self.xero_client = XeroAPI(self.platform.client_id, ...)

    async def authenticate(self) -> bool:
        """Handle OAuth2 flow with Xero"""

    async def get_contacts(self, updated_since: datetime) -> List[Contact]:
        """Fetch contacts from Xero and normalize to standard format"""
        xero_contacts = self.xero_client.get_contacts()
        return [self.mapper.xero_contact_to_standard(c) for c in xero_contacts]

    # ... implement all required methods
```

2. **auth.py - OAuth2 Handler**
```python
class XeroOAuth:
    """Handle Xero OAuth2 authentication"""

    async def get_authorization_url(self, state: str) -> str:
        """Generate OAuth authorization URL"""

    async def get_access_token(self, auth_code: str) -> Token:
        """Exchange auth code for access token"""

    async def refresh_access_token(self, refresh_token: str) -> Token:
        """Refresh expired access token"""
```

3. **mapper.py - Data Normalization**
```python
class XeroMapper:
    """Convert Xero data to standard models"""

    @staticmethod
    def xero_contact_to_standard(xero_contact) -> Contact:
        """Map Xero Contact to standard Contact model"""

    @staticmethod
    def xero_invoice_to_standard(xero_invoice) -> Transaction:
        """Map Xero Invoice to standard Transaction model"""

    # ... etc for all Xero data types
```

**Steps:**
```bash
1. Create client.py with XeroClient class
2. Implement authenticate() method
3. Implement get_contacts() method
4. Implement get_transactions() method
5. Implement get_accounts() method
6. Create auth.py with OAuth handling
7. Create mapper.py with data normalization
8. Write tests using mock Xero API
9. Test with actual Xero API (sandbox if available)
```

**Deliverables:**
- XeroClient class implementing AccountingClient
- OAuth2 authentication working
- All 4 main methods implemented
- Data mappers normalizing Xero data
- Unit tests passing

**Success Criteria:**
- XeroClient can authenticate with Xero
- get_contacts() returns normalized data
- get_transactions() returns normalized data
- get_accounts() returns normalized data
- All data validates against standard models
- Unit tests pass (100%)

---

### Task 6: Create Mock Client Test Data
**Priority:** MEDIUM - Needed for testing
**Time Estimate:** 1 hour
**Status:** Ready to create

**What This Does:**
- Creates test data in mock-clients/ folder
- Provides realistic sample data
- Enables testing without live API calls
- Helps design UI later

**Folders to Create:**
```
mock-clients/
├── xero/
│   └── example-bookkeeper/
│       ├── transactions.json      # Sample transactions
│       ├── contacts.json          # Sample customers/suppliers
│       └── accounts.json          # Chart of accounts
└── quickbooks/
    └── example-practice/
        ├── transactions.json
        ├── contacts.json
        └── accounts.json
```

**Sample Data:**
```json
{
  "contacts": [
    {
      "id": "xero-001",
      "platform_id": "4f5f0e2a-c8c5-45df-a9b2-8f7c3d5e9a1b",
      "platform_name": "xero",
      "name": "Example Cafe Ltd",
      "email": "contact@examplecafe.com",
      "contact_type": "customer"
    }
  ],
  "transactions": [
    {
      "id": "txn-001",
      "platform_id": "7c3f8e2a-d5e9-45df-a9b2-8f7c3d5e9a2c",
      "platform_name": "xero",
      "transaction_type": "invoice",
      "amount": 1250.00,
      "date": "2025-11-20",
      "status": "submitted"
    }
  ]
}
```

**Steps:**
```bash
1. Create JSON files with sample data
2. Follow DATABASE_SCHEMA.md structure
3. Include 5-10 contacts
4. Include 10-20 transactions
5. Include accounts
6. Create README explaining data
```

**Deliverables:**
- Sample JSON files in mock-clients/
- README explaining mock data
- Ready for unit tests
- Ready for API testing

**Success Criteria:**
- Data is realistic
- Data validates against models
- Can be loaded into tests
- No sensitive real data

---

### Task 7: Write Unit Tests
**Priority:** HIGH - Quality assurance from day 1
**Time Estimate:** 2 hours
**Status:** Framework ready, ready to write

**What This Does:**
- Ensures code works correctly
- Documents expected behavior
- Prevents regressions
- Increases confidence

**Tests to Create:**
```
tests/
├── test_accounting/
│   ├── test_base.py             # Test abstract class
│   ├── test_factory.py          # Test factory pattern
│   └── test_xero_client.py      # Test Xero client
├── test_models/
│   ├── test_organization.py
│   ├── test_transaction.py
│   └── test_client_model.py
└── conftest.py                  # Shared fixtures
```

**Test Strategy:**
```python
# Example test structure

def test_factory_creates_xero_client():
    """Factory should create XeroClient for 'xero' platform"""
    factory = AccountingClientFactory()
    client = factory.create('xero', credentials)
    assert isinstance(client, XeroClient)

def test_contact_model_validation():
    """Contact model should validate required fields"""
    contact = Contact(name="Test", email="test@example.com")
    assert contact.name == "Test"

async def test_xero_client_authenticate():
    """XeroClient should authenticate with credentials"""
    client = XeroClient(org)
    result = await client.authenticate()
    assert result is True
```

**Steps:**
```bash
1. Create conftest.py with fixtures
2. Create test_base.py
3. Create test_factory.py
4. Create test_models for each model
5. Create test_xero_client.py
6. Run: pytest tests/
7. Aim for >80% coverage
```

**Deliverables:**
- 20+ unit tests
- Test fixtures for reusability
- Mock Xero API responses
- Test database

**Success Criteria:**
- All tests pass
- Coverage >80%
- Tests are clear and documented
- Can run tests with: `pytest tests/ -v`

---

## 📊 WEEK-BY-WEEK BREAKDOWN

### Week 2 (Next)
**Focus:** Database Foundation

- [ ] Task 1: Initialize Alembic (45 min)
- [ ] Task 2: Create SQLAlchemy Models (1.5 hours)
- [ ] Commit: "Create database models and migrations"
- **Expected Result:** Database schema in PostgreSQL, models in code

### Week 3
**Focus:** API Foundation + Abstraction

- [ ] Task 3: Set Up FastAPI (1 hour)
- [ ] Task 4: Build Abstraction Layer (2 hours)
- [ ] Commit: "Create API foundation and abstraction layer"
- **Expected Result:** Running API, platform-independent interface

### Week 4-5
**Focus:** Xero Integration + Testing

- [ ] Task 5: Develop Xero Adapter (2-3 hours)
- [ ] Task 6: Create Mock Data (1 hour)
- [ ] Task 7: Write Unit Tests (2 hours)
- [ ] Commit: "Add Xero adapter and tests"
- **Expected Result:** Functional Xero integration, >80% test coverage

### Week 6-8
**Focus:** Testing + Polish + Documentation

- [ ] Run full integration tests
- [ ] Performance testing
- [ ] Documentation completeness
- [ ] Code review for standards
- [ ] Commit: "Phase 1 complete - Foundation ready"
- **Expected Result:** Production-ready foundation for Phase 2

---

## 🎯 SUCCESS CRITERIA FOR PHASE 1

Phase 1 is complete when:

1. ✅ Database
   - [ ] Alembic migrations working
   - [ ] All 9 tables created
   - [ ] No schema warnings

2. ✅ Code
   - [ ] FastAPI running without errors
   - [ ] All models validating
   - [ ] Factory pattern working
   - [ ] Xero adapter functional

3. ✅ Tests
   - [ ] 20+ tests written
   - [ ] 80%+ coverage
   - [ ] All tests passing

4. ✅ Documentation
   - [ ] Code documented
   - [ ] README updated
   - [ ] API docs auto-generated

5. ✅ Integration
   - [ ] Can fetch Xero contacts
   - [ ] Can fetch Xero transactions
   - [ ] Data normalizes correctly

---

## 💻 HOW TO EXECUTE EACH TASK

### General Process for Each Task

**Step 1: Read the Documentation**
```bash
# Before starting a task, read:
1. This roadmap section
2. Related documentation
3. DATABASE_SCHEMA.md (if database task)
4. PROJECT_INIT.md (standards)
```

**Step 2: Plan the Code**
```bash
# Break down the task:
1. Identify files to create
2. Identify classes/functions needed
3. Identify tests needed
4. Sketch the architecture
```

**Step 3: Write the Code**
```bash
# Implement:
1. Create the files
2. Add type hints
3. Add docstrings
4. Follow style guide (black, flake8)
```

**Step 4: Write Tests**
```bash
# Test immediately:
1. Unit tests for each function
2. Integration tests for features
3. Run: pytest tests/ -v --cov
```

**Step 5: Commit**
```bash
# Save your work:
git add .
git commit -m "[FEAT] Task description

Brief explanation of what was done
and why it matters."
```

**Step 6: Update Documentation**
```bash
# Record completion:
1. Update SESSION_YYYY-MM-DD.md
2. Note any issues/decisions
3. Update README if needed
```

---

## 🚀 READY TO START?

### Option A: Start Immediately
```bash
# Ready to begin Task 1?
# I'll guide you through every step
# Type: "Yes, let's start Task 1"
```

### Option B: Understand First
```bash
# Want to understand all tasks first?
# I can explain the architecture more
# Type: "Explain more about the architecture"
```

### Option C: Customize Approach
```bash
# Want to change the order?
# Want to start with different task?
# Type: "I want to start with [task name]"
```

---

## 📝 DAILY WORKFLOW

For each working session:

```bash
1. Read previous session's notes
   ls docs/SESSION_*.md

2. Activate virtual environment
   source venv/Scripts/activate

3. Check git status
   git status

4. Work on assigned task
   [implement code]

5. Run tests
   pytest tests/ -v

6. Check code quality
   black . && flake8 . && mypy .

7. Commit your work
   git add . && git commit -m "..."

8. Update session journal
   # Edit docs/SESSION_YYYY-MM-DD.md

9. Push to git (when ready)
   git push
```

---

## ⚠️ IMPORTANT NOTES

1. **One Task at a Time**
   - Complete Task 1 before starting Task 2
   - Tests must pass before moving forward
   - Commit after each task

2. **Follow Standards**
   - Type hints on all functions
   - Docstrings on all classes/functions
   - Tests for all logic
   - Follow PROJECT_INIT.md standards

3. **Document as You Go**
   - Update session journal daily
   - Note decisions and rationale
   - Record any issues found

4. **Quality Over Speed**
   - Tests passing > code written faster
   - Clear code > clever code
   - Documented > undocumented

---

**Next Step:** Choose which task to start with, and I'll guide you through every step.

**Questions?** Ask before starting - clarity prevents rework.

---

**Created:** November 23, 2025
**Valid Until:** Next major milestone
**Maintainer:** Project Lead + Claude Code

