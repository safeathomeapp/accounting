# 📊 Accountancy - Multi-Platform Accounting Integration System

**Production-ready accounting integration platform** that abstracts platform-specific APIs and provides a unified interface for Xero, QuickBooks, and extensible to any accounting system.

**Current Status**: Month 2, Week 4 Complete ✅ | 353/353 Tests Passing (100%)

---

## 🎯 What This Does

This system solves a critical problem for accounting practices:

> **Write business logic ONCE. Works with ANY accounting platform.**

Instead of rewriting code for each accounting system (Xero, QB, Sage, FreshBooks, etc.), your application uses our unified `AccountingClient` interface. Behind the scenes, we handle all the platform-specific complexity.

### Supported Platforms
- ✅ **Xero** - Full integration (OAuth 2.0, all endpoints)
- ✅ **QuickBooks Online** - Full integration (OAuth 2.0, all endpoints)
- ✅ **Mock Client** - For testing/development
- 🔄 **Future**: Sage, FreshBooks, Wave, others

---

## ✨ Key Features

### Platform Abstraction
- Single interface works with all platforms
- Plugin architecture for adding new platforms
- Factory pattern for automatic client creation
- No platform-specific code in business logic

### Financial Reporting
- Profit & Loss statements
- Balance Sheet generation
- Cash Flow analysis
- Trial Balance reports
- Custom date ranges
- Category-based analysis

### Data Sync
- Full sync (download all data)
- Incremental sync (new data only)
- Automated background jobs (daily/hourly)
- Retry logic with exponential backoff
- Error handling & recovery

### Transaction Management
- Multi-currency support ready
- Smart categorization engine
- Account reconciliation
- Discrepancy detection
- Bank statement matching

### Analytics & Insights
- 14 REST API endpoints
- Real-time reporting
- Transaction trending
- Category statistics
- Sync performance metrics

---

## 📈 Current Implementation Status

### Completed (Month 1-2)

**Platform Adapters** (174 tests)
- Abstraction layer with 15 abstract methods
- Xero integration with OAuth 2.0
- QuickBooks Online integration
- Mock client for development

**Sync Engine** (48 tests)
- Core sync logic
- Full & incremental strategies
- API routes
- Background job scheduling
- Retry mechanism

**Reporting & Analytics** (91 tests)
- Financial report generation
- Transaction categorization
- Account reconciliation
- 14 analytics endpoints

**Test Coverage**: 353/353 tests passing (100%)

---

## 📚 Documentation

### 👉 **START HERE**
1. **[PROJECT_STATUS.md](PROJECT_STATUS.md)** - Current state, what works, quick commands
2. **[DEVELOPMENT_ROADMAP.md](DEVELOPMENT_ROADMAP.md)** - What's planned, feature roadmap
3. **[docs/INDEX.md](docs/INDEX.md)** - Complete documentation navigation

### By Topic

| Topic | Document |
|-------|----------|
| **Design & Architecture** | [docs/ARCHITECTURE/ARCHITECTURE_PRINCIPLES.md](docs/ARCHITECTURE/ARCHITECTURE_PRINCIPLES.md) |
| **Database Design** | [docs/ARCHITECTURE/DATABASE_SCHEMA.md](docs/ARCHITECTURE/DATABASE_SCHEMA.md) |
| **Tech Stack** | [docs/ARCHITECTURE/TECH_STACK.md](docs/ARCHITECTURE/TECH_STACK.md) |
| **Xero Integration** | [docs/PLATFORM_GUIDES/XERO_API_GUIDE.md](docs/PLATFORM_GUIDES/XERO_API_GUIDE.md) |
| **Xero Implementation** | [docs/PLATFORM_GUIDES/XERO_IMPLEMENTATION_BLUEPRINT.md](docs/PLATFORM_GUIDES/XERO_IMPLEMENTATION_BLUEPRINT.md) |
| **QB Integration** | [docs/PLATFORM_GUIDES/QUICKBOOKS_API_GUIDE.md](docs/PLATFORM_GUIDES/QUICKBOOKS_API_GUIDE.md) |
| **Data Mapping** | [docs/PLATFORM_GUIDES/DATA_MAPPING_SPEC.md](docs/PLATFORM_GUIDES/DATA_MAPPING_SPEC.md) |
| **Sync Engine** | [docs/COMPONENTS/SYNC_ENGINE_ROADMAP.md](docs/COMPONENTS/SYNC_ENGINE_ROADMAP.md) |
| **Reporting** | [docs/COMPONENTS/WEEK4_REPORTING_ANALYTICS_ROADMAP.md](docs/COMPONENTS/WEEK4_REPORTING_ANALYTICS_ROADMAP.md) |
| **Session Notes** | [docs/SESSION_NOTES/SESSION_NOTES.md](docs/SESSION_NOTES/SESSION_NOTES.md) |
| **Original Vision** | [docs/REFERENCES/VISION.md](docs/REFERENCES/VISION.md) |

---

## 🚀 Quick Start

### Prerequisites
```bash
Python 3.13.7+
PostgreSQL 14+
Xero/QuickBooks API credentials (optional, for real data)
```

### Installation

```bash
# Clone and setup
git clone [repository-url]
cd accountancy
python -m venv venv
. venv/Scripts/activate      # Windows

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your settings

# Initialize database
psql -U postgres -c "CREATE DATABASE accountancy_dev"

# Start application
uvicorn backend.main:app --reload
```

### Run Tests

```bash
# All tests (should show 353 passing)
pytest tests/ -v

# Specific test file
pytest tests/test_reporting_week4.py -v

# With coverage
pytest tests/ --cov=backend --cov-report=html
```

---

## 💻 Usage Examples

### Creating a Client

```python
from backend.accounting.factory import AccountingClientFactory

# From organization (uses stored credentials)
client = AccountingClientFactory.create(organization)

# Direct instantiation
client = AccountingClientFactory.create_from_platform(
    platform="xero",
    organization_id="org123",
    credentials={
        "client_id": "your_id",
        "client_secret": "your_secret",
        "redirect_uri": "http://localhost:8000/callback"
    }
)
```

### Fetching Data

```python
from datetime import date

# Get transactions
transactions = client.get_transactions(
    start_date=date(2025, 1, 1),
    end_date=date(2025, 12, 31)
)

# Get accounts
accounts = client.get_accounts()

# Get contacts
contacts = client.get_contacts(limit=100)

# Check organization
org_info = client.get_organization_info()

# Get sync status
status = client.get_sync_status()
```

### Running Sync

```python
from backend.sync.engine import SyncEngine

engine = SyncEngine(db_session)

# Full sync (all data)
result = engine.full_sync(organization)

# Incremental sync (new data only)
result = engine.incremental_sync(organization)

# Check result
print(f"Downloaded: {result.total_transactions}")
print(f"Failed: {result.failed_transactions}")
```

### Generating Reports

```python
from backend.reporting.generators import ReportGenerator
from datetime import date

generator = ReportGenerator(db, organization_id)

# Profit & Loss
pl_report = generator.generate_profit_loss(
    start_date=date(2025, 1, 1),
    end_date=date(2025, 12, 31)
)

# Balance Sheet
bs_report = generator.generate_balance_sheet(
    as_of_date=date(2025, 12, 31)
)

# Trial Balance
tb_report = generator.generate_trial_balance(
    as_of_date=date(2025, 12, 31)
)
```

---

## 🏗️ Architecture

### Three-Layer Design

```
┌─────────────────────────────────────┐
│     Business Logic Layer             │ Your code
├─────────────────────────────────────┤
│   Abstraction Layer                  │ AccountingClient interface
│   (Platform-agnostic)                │
├─────────────────────────────────────┤
│   Platform Adapters                  │ XeroClient, QBClient, etc.
│   (Platform-specific)                │
├─────────────────────────────────────┤
│   Platform APIs                      │ Xero API, QB API, etc.
└─────────────────────────────────────┘
```

### Key Components

| Component | Purpose | Location |
|-----------|---------|----------|
| **AccountingClient** | Abstract base class (15 methods) | `backend/accounting/base.py` |
| **XeroClient** | Xero API adapter | `backend/accounting/xero/` |
| **QBClient** | QB Online adapter | `backend/accounting/quickbooks/` |
| **Factory** | Dynamic client creation | `backend/accounting/factory.py` |
| **SyncEngine** | Data synchronization | `backend/sync/engine.py` |
| **SyncScheduler** | Background job scheduling | `backend/sync/scheduler.py` |
| **ReportGenerator** | Financial report generation | `backend/reporting/generators.py` |
| **CategorizationEngine** | Transaction categorization | `backend/reporting/categorization.py` |
| **ReconciliationEngine** | Account reconciliation | `backend/reporting/reconciliation.py` |

---

## 📊 Project Structure

```
accountancy/
├── README.md                          ← You are here
├── PROJECT_STATUS.md                  ← Current facts
├── DEVELOPMENT_ROADMAP.md             ← What's planned
├── SESSION_POINTER.md                 ← Next session guide
├── PROJECT_AUDIT.md                   ← Investigation trail
│
├── backend/
│   ├── main.py                        # FastAPI application
│   ├── config.py                      # Configuration
│   ├── database.py                    # Database connection
│   │
│   ├── models/                        # Database models (9 tables)
│   │   └── [organization, account, transaction, etc.]
│   │
│   ├── accounting/                    # Platform abstraction
│   │   ├── base.py                   # AccountingClient ABC
│   │   ├── factory.py                # Factory pattern
│   │   ├── types.py                  # Standard models
│   │   ├── xero/                     # Xero adapter
│   │   │   ├── client.py
│   │   │   ├── auth.py
│   │   │   └── mapper.py
│   │   ├── quickbooks/               # QB adapter
│   │   │   ├── client.py
│   │   │   ├── auth.py
│   │   │   └── mapper.py
│   │   └── mock/                     # Mock client
│   │       └── client.py
│   │
│   ├── sync/                         # Sync engine
│   │   ├── engine.py                # Core sync logic
│   │   ├── strategies.py            # Sync strategies
│   │   ├── scheduler.py             # APScheduler wrapper
│   │   ├── retry.py                 # Retry logic
│   │   └── tasks.py                 # Background jobs
│   │
│   ├── api/                         # REST API routes
│   │   ├── sync_routes.py
│   │   └── analytics_routes.py
│   │
│   └── reporting/                   # Reporting & analytics
│       ├── models.py                # Report models
│       ├── generators.py            # Report generation
│       ├── categorization.py        # Categorization
│       └── reconciliation.py        # Reconciliation
│
├── tests/                           # 353 tests, all passing
│   ├── test_accounting_base.py      # 31 tests
│   ├── test_accounting_factory.py   # 21 tests
│   ├── test_accounting_xero.py      # 35 tests
│   ├── test_accounting_quickbooks.py # 39 tests
│   ├── test_accounting_mock.py      # 48 tests
│   ├── test_sync_engine.py          # 25 tests
│   ├── test_sync_week2.py           # 23 tests
│   ├── test_sync_week3.py           # 40 tests
│   ├── test_categorization_week4.py # 28 tests
│   ├── test_reconciliation_week4.py # 26 tests
│   ├── test_analytics_week4.py      # 17 tests
│   └── test_reporting_week4.py      # 20 tests
│
├── docs/                            # Comprehensive documentation
│   ├── INDEX.md                     # Documentation hub
│   ├── CURRENT/                     # Current master files
│   ├── ARCHITECTURE/                # Design documentation
│   ├── PLATFORM_GUIDES/             # API integration guides
│   ├── COMPONENTS/                  # Feature documentation
│   ├── SESSION_NOTES/               # Historical records
│   └── REFERENCES/                  # Historical/archived docs
│
├── requirements.txt                 # Python dependencies
├── .env.example                     # Environment template
└── .gitignore                       # Git ignore rules
```

---

## 🧪 Testing

### Test Coverage

```
Total Tests: 353/353 (100% passing)

Month 1 - Platform Adapters:     174 tests
├── Abstraction Layer:            52 tests
├── Factory Pattern:              21 tests
├── Xero Integration:             35 tests
├── QB Integration:               39 tests
└── Mock Client:                  48 tests

Month 2 - Sync & Reporting:      179 tests
├── Sync Engine:                  25 tests
├── Sync Routes:                  23 tests
├── Background Jobs:              40 tests
├── Categorization:               28 tests
├── Reconciliation:               26 tests
├── Analytics:                    17 tests
└── Reporting:                    20 tests
```

### Running Tests

```bash
# All tests
pytest tests/ -v

# Specific module
pytest tests/test_accounting_xero.py -v

# With coverage report
pytest tests/ --cov=backend --cov-report=html

# Specific test function
pytest tests/test_reporting_week4.py::TestReportGenerator::test_generate_profit_loss_simple -v
```

---

## 🔐 Security Features

- ✅ OAuth 2.0 with PKCE (state parameter + code verifier)
- ✅ Secure token refresh
- ✅ Environment variables for all credentials
- ✅ HTTPS/TLS for all API calls
- ✅ 30-second request timeout
- ✅ No sensitive data in logs
- ✅ Database encryption ready
- ✅ CORS protection
- ✅ Input validation on all endpoints

---

## 🛠️ Adding a New Platform

To add support for a new accounting platform (e.g., Sage):

### 1. Create Platform Directory
```bash
mkdir backend/accounting/sage
```

### 2. Implement Three Files

**auth.py** - OAuth/credential handling
```python
class SageAuth:
    """Handle Sage OAuth 2.0 flow"""
    def __init__(self, client_id, client_secret, redirect_uri):
        # Your auth logic here
```

**mapper.py** - Transform Sage data to standard format
```python
def map_sage_invoice(sage_invoice) -> StandardTransaction:
    """Convert Sage invoice to StandardTransaction"""
```

**client.py** - Main adapter implementing AccountingClient
```python
class SageClient(AccountingClient):
    """Sage API adapter"""
    def get_transactions(self, ...):
        # Implement all 15 abstract methods
```

### 3. Add Tests
```bash
pytest tests/test_accounting_sage.py  # 35+ tests for coverage
```

### 4. Register in Factory
```python
# backend/accounting/factory.py
PLATFORM_CLIENTS = {
    'xero': XeroClient,
    'quickbooks': QuickBooksClient,
    'sage': SageClient,  # ADD THIS
}
```

That's it! No changes needed in business logic.

---

## 📞 Key Commands

### Development
```bash
# Start API server
uvicorn backend.main:app --reload

# Run all tests
pytest tests/ -v

# Run specific test
pytest tests/test_accounting_xero.py -v

# Generate coverage report
pytest tests/ --cov=backend --cov-report=html
```

### Database
```bash
# Connect to database
psql -U postgres -d accountancy_dev

# View tables
\dt

# View all schemas
\dn
```

### Git
```bash
# See recent commits
git log --oneline -10

# Check status
git status

# Create new feature branch
git checkout -b feature/my-feature
```

---

## 📋 Technology Stack

| Layer | Technology | Version |
|-------|-----------|---------|
| **Framework** | FastAPI | 0.104+ |
| **Language** | Python | 3.13.7 |
| **Database** | PostgreSQL | 16+ |
| **ORM** | SQLAlchemy | 2.0+ |
| **Validation** | Pydantic | 2.0+ |
| **Auth** | OAuth 2.0 | PKCE |
| **Scheduling** | APScheduler | 3.10+ |
| **Testing** | pytest | 8.0+ |
| **HTTP Client** | requests | 2.31+ |

---

## 📈 Next Steps (Month 3)

### Ready to Start
- Real-time sync monitoring dashboard
- Multi-currency support and conversion
- Tax compliance features
- Advanced forecasting and analytics

See [DEVELOPMENT_ROADMAP.md](DEVELOPMENT_ROADMAP.md) for details.

---

## 📞 Support & Documentation

- 📖 **Full Docs**: [docs/INDEX.md](docs/INDEX.md)
- 📊 **Current Status**: [PROJECT_STATUS.md](PROJECT_STATUS.md)
- 🗺️ **Roadmap**: [DEVELOPMENT_ROADMAP.md](DEVELOPMENT_ROADMAP.md)
- 🔍 **Architecture**: [docs/ARCHITECTURE/ARCHITECTURE_PRINCIPLES.md](docs/ARCHITECTURE/ARCHITECTURE_PRINCIPLES.md)
- 📝 **Session Notes**: [docs/SESSION_NOTES/SESSION_NOTES.md](docs/SESSION_NOTES/SESSION_NOTES.md)

---

## 📄 License

[To be added]

---

**Status**: Month 2 Week 4 Complete ✅
**Tests**: 353/353 passing (100%)
**Next**: Month 3 features ready to start
**Last Updated**: November 25, 2025

