# Accountancy - Multi-Platform Accounting Integration

A production-grade accounting integration system that abstracts away platform-specific APIs and provides a unified interface for multiple accounting software platforms.

## Overview

This project implements a plugin architecture for accounting integrations, currently supporting:
- **Xero** (Fully Implemented - Week 3)
- **QuickBooks** (Roadmapped - Week 7)
- **Mock Client** (Roadmapped - Week 4)

The system is built around an abstraction layer that allows business logic to remain platform-agnostic while seamlessly supporting multiple accounting platforms.

## Project Status

### Completed (Month 1)
- **Week 1**: Environment setup (Python 3.13.7, PostgreSQL, FastAPI)
- **Week 2**: Abstraction layer with 52 comprehensive tests
- **Week 3**: XeroClient implementation with 35 tests

**Current Metrics:**
- Tests: 87/87 passing (100%)
- Code Coverage: 72%
- Supported Platforms: 1 (Xero)

### Roadmap
- **Week 4**: Mock Client implementation
- **Week 5**: QuickBooks Phase 1
- **Month 2-3**: Advanced features (multi-platform sync, reporting)
- **Month 12**: Sage, FreeAgent, and other platforms

## Quick Start

### Prerequisites
- Python 3.13.7+
- PostgreSQL
- Xero API credentials (for Xero integration)

### Installation

```bash
git clone https://github.com/safeathomeapp/accounting.git
cd accounting
python -m venv venv
source venv/Scripts/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your settings
uvicorn backend.main:app --reload
```

### Testing

```bash
pytest tests/ -v                                           # All tests
pytest tests/test_accounting_xero.py -v                   # Xero only
pytest tests/ --cov=backend.accounting --cov-report=html  # Coverage
```

## Usage

### Creating a Client

```python
from backend.accounting.factory import AccountingClientFactory

# Option 1: From organization
client = AccountingClientFactory.create(organization)

# Option 2: Direct instantiation
credentials = {
    "client_id": "your_client_id",
    "client_secret": "your_client_secret",
    "redirect_uri": "http://localhost:8000/auth/xero/callback"
}
client = AccountingClientFactory.create_from_platform(
    platform="xero",
    organization_id="org123",
    credentials=credentials
)
```

### Fetching Data

```python
from datetime import date
from backend.accounting import TransactionType

# Get transactions
transactions = client.get_transactions(
    start_date=date(2025, 1, 1),
    end_date=date(2025, 1, 31),
    transaction_types=[TransactionType.INVOICE]
)

# Get contacts
contacts = client.get_contacts(limit=100)

# Get accounts
accounts = client.get_accounts()

# Get organization info
org_info = client.get_organization_info()

# Check sync status
status = client.get_sync_status()
```

## Architecture

### Three-Layer Design

```
Business Logic Layer
        ↓
Abstraction Layer (AccountingClient interface)
        ↓
Platform Adapters (XeroClient, QuickBooksClient, etc.)
        ↓
Platform APIs
```

### Key Components

- **AccountingClient**: Abstract base class (15 abstract methods)
- **Standard Models**: Transaction, Contact, Account, SyncStatus
- **Factory Pattern**: Dynamic client instantiation
- **Platform Adapters**: Xero, QuickBooks (roadmapped), Mock (roadmapped)

## Documentation

See `/docs` folder:

- `START_HERE.md` - Project overview and quick reference
- `ARCHITECTURE_PRINCIPLES.md` - Design patterns
- `MULTI_PLATFORM_ROADMAP.md` - 12-month plan
- `XERO_API_GUIDE.md` - Xero integration details
- `XERO_IMPLEMENTATION_BLUEPRINT.md` - Implementation steps
- `SESSION_2025-11-24.md` - Week 3 completion summary

## Project Structure

```
accounting/
├── backend/
│   ├── main.py                 # FastAPI app
│   ├── accounting/
│   │   ├── base.py            # AccountingClient ABC
│   │   ├── factory.py         # Factory pattern
│   │   └── xero/              # Xero adapter
│   │       ├── auth.py        # OAuth 2.0
│   │       ├── mapper.py      # Data transformation
│   │       └── client.py      # Main adapter
├── tests/
│   ├── test_accounting_base.py        # 31 tests
│   ├── test_accounting_factory.py     # 21 tests
│   └── test_accounting_xero.py        # 35 tests
├── docs/
├── requirements.txt
├── .env.example
└── README.md
```

## Features

### Xero Integration
- OAuth 2.0 with PKCE
- Automatic token refresh
- Transaction fetching (invoices, bills, bank transfers)
- Contact management
- Chart of accounts
- Rate limit tracking (60 calls/minute)
- Pagination support
- Comprehensive error handling

### Standard Models
- `StandardTransaction` - Invoices, bills, transfers
- `StandardContact` - Customers, suppliers
- `StandardAccount` - Chart of accounts
- `SyncStatus` - Metadata

### Error Handling
- `AuthenticationError` - Auth failures
- `APIError` - General API errors
- `RateLimitError` - Rate limit exceeded
- `NotFoundError` - Resource not found
- `ValidationError` - Input validation

## Testing

```
Test Results:
- Abstraction Layer:  31 tests, 100% passing
- Factory Pattern:    21 tests, 100% passing
- Xero Client:       35 tests, 100% passing
TOTAL:               87 tests, 100% passing
```

Coverage: 72% overall (Mapper: 91%, Client: 78%)

## Code Quality

- Type hints on all functions
- Docstrings on all classes/methods
- Platform-agnostic business logic
- Plugin architecture
- 80%+ test coverage target
- Comprehensive error handling

## Contributing

To add a new platform:

1. Create `backend/accounting/<platform>/` with auth.py, mapper.py, client.py
2. Implement `<Platform>Client` extending `AccountingClient`
3. Add tests with 80%+ coverage
4. Add to `PLATFORM_CLIENTS` in factory.py
5. Update documentation

That's it! No other code changes needed.

## Environment Variables

```env
DATABASE_URL=postgresql://user:password@localhost/accountancy_dev
XERO_CLIENT_ID=your_client_id
XERO_CLIENT_SECRET=your_client_secret
XERO_REDIRECT_URI=http://localhost:8000/auth/xero/callback
DEBUG=True
SECRET_KEY=your_secret_key
```

## Security

- Credentials stored in environment variables only
- OAuth 2.0 with PKCE
- Secure token refresh
- No sensitive data in logs
- 30-second request timeout
- Database encryption

## License

[To be added]

## Support

- Check `START_HERE.md` for quick reference
- Read `/docs` for detailed documentation
- Review tests for usage examples
- Check session notes for recent work

---

**Status**: Week 3 Complete - Ready for Week 4
**Tests**: 87/87 passing
**Last Updated**: November 24, 2025
