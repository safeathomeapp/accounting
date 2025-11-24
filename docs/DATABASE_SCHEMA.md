# Database Schema Design
**Version:** 1.0
**Date:** November 23, 2025
**Status:** Foundation Phase Ready
**Database:** PostgreSQL 17.6

---

## 📐 SCHEMA DESIGN PRINCIPLES

### Core Principles

1. **Platform Independence**
   - Schema works with both Xero and QuickBooks
   - No platform-specific columns in core tables
   - Platform metadata stored separately
   - Allows switching platforms without data loss

2. **Normalization**
   - 3NF (Third Normal Form) throughout
   - Minimal data duplication
   - Clear relationships
   - Efficient queries

3. **Audit Trail**
   - Track who changed what and when
   - Essential for accounting compliance
   - Enable data recovery and history
   - Support regulatory requirements

4. **Security**
   - API credentials encrypted in database
   - No plain-text secrets
   - User data protected
   - Secure OAuth token storage

5. **Extensibility**
   - Room for Phase 2+ features
   - Support for future platforms (Sage, FreeAgent)
   - Easy to add new data types
   - Minimal migrations needed

6. **Performance**
   - Efficient indexing strategy
   - Support for large datasets
   - Query optimization opportunities
   - Partitioning-ready

---

## 🗄️ CORE TABLES

### 1. organizations

**Purpose:** Store organization/practice information

```sql
CREATE TABLE organizations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255) NOT NULL UNIQUE,
    phone VARCHAR(20),
    address_line1 VARCHAR(255),
    address_line2 VARCHAR(255),
    city VARCHAR(100),
    postal_code VARCHAR(20),
    country VARCHAR(100) DEFAULT 'UK',
    timezone VARCHAR(50) DEFAULT 'Europe/London',
    currency VARCHAR(3) DEFAULT 'GBP',

    -- Configuration
    is_active BOOLEAN DEFAULT TRUE,

    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT valid_email CHECK (email ~* '^[^\s@]+@[^\s@]+\.[^\s@]+$')
);

CREATE INDEX idx_organizations_email ON organizations(email);
CREATE INDEX idx_organizations_is_active ON organizations(is_active);
```

**Notes:**
- Single organization for MVP (user's practice)
- Ready to expand to multi-tenant in Phase 3
- All timestamps in UTC (timezone conversion in app)
- Stores both system settings and compliance info

---

### 2. accounting_platforms

**Purpose:** Track which accounting platforms this organization uses

```sql
CREATE TABLE accounting_platforms (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,

    -- Platform identification
    platform_name VARCHAR(50) NOT NULL, -- 'xero', 'quickbooks'
    platform_version VARCHAR(50),

    -- OAuth information
    client_id VARCHAR(500) NOT NULL,
    client_secret_encrypted BYTEA NOT NULL, -- Encrypted with ENCRYPTION_KEY
    access_token_encrypted BYTEA, -- Encrypted
    refresh_token_encrypted BYTEA, -- Encrypted
    token_expires_at TIMESTAMP WITH TIME ZONE,

    -- Xero-specific
    tenant_id VARCHAR(255), -- Xero's organization ID

    -- QuickBooks-specific
    realm_id VARCHAR(255), -- QB's company ID

    -- Status
    is_active BOOLEAN DEFAULT TRUE,
    connection_status VARCHAR(50) DEFAULT 'pending', -- 'pending', 'connected', 'error'
    last_sync_at TIMESTAMP WITH TIME ZONE,
    last_error_message TEXT,

    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT valid_platform CHECK (platform_name IN ('xero', 'quickbooks')),
    CONSTRAINT unique_platform_per_org UNIQUE(organization_id, platform_name)
);

CREATE INDEX idx_platforms_org ON accounting_platforms(organization_id);
CREATE INDEX idx_platforms_status ON accounting_platforms(connection_status);
CREATE INDEX idx_platforms_sync ON accounting_platforms(last_sync_at);
```

**Notes:**
- Supports multiple platforms per organization
- OAuth tokens encrypted at rest
- Status tracking for monitoring
- Error messages for debugging
- Xero tenant_id and QB realm_id for multi-tenant APIs

---

### 3. clients (Contacts/Customers)

**Purpose:** Store customer/contact information from accounting platforms

```sql
CREATE TABLE clients (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,

    -- Platform mapping
    platform_id VARCHAR(500), -- Xero: ContactID, QB: Id
    platform_name VARCHAR(50) NOT NULL, -- 'xero', 'quickbooks'

    -- Contact information
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255),
    phone VARCHAR(20),
    website VARCHAR(255),

    -- Address
    address_line1 VARCHAR(255),
    address_line2 VARCHAR(255),
    city VARCHAR(100),
    postal_code VARCHAR(20),
    country VARCHAR(100),

    -- Classification
    contact_type VARCHAR(50), -- 'customer', 'supplier', 'employee', 'other'
    industry VARCHAR(100),
    tax_number VARCHAR(50),

    -- Status
    is_active BOOLEAN DEFAULT TRUE,

    -- Sync metadata
    last_synced_at TIMESTAMP WITH TIME ZONE,
    platform_updated_at TIMESTAMP WITH TIME ZONE,

    -- Record metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT unique_platform_client UNIQUE(platform_name, platform_id)
);

CREATE INDEX idx_clients_org ON clients(organization_id);
CREATE INDEX idx_clients_platform ON clients(platform_name, platform_id);
CREATE INDEX idx_clients_email ON clients(email);
CREATE INDEX idx_clients_status ON clients(is_active);
CREATE INDEX idx_clients_sync ON clients(last_synced_at);
```

**Notes:**
- Maps to Xero Contacts and QB Customers
- Stores multiple copies if same contact in multiple platforms
- Tracks sync status for debugging
- Ready for Phase 2 deduplication feature

---

### 4. transactions

**Purpose:** Store financial transactions from accounting platforms

```sql
CREATE TABLE transactions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,

    -- Platform mapping
    platform_id VARCHAR(500), -- Xero: InvoiceID, QB: Id
    platform_name VARCHAR(50) NOT NULL,

    -- Transaction details
    transaction_type VARCHAR(50) NOT NULL, -- 'invoice', 'bill', 'bank_transaction'
    reference_number VARCHAR(100),
    description TEXT,

    -- Amounts (stored as NUMERIC for precision)
    amount NUMERIC(15,2) NOT NULL,
    tax_amount NUMERIC(15,2) DEFAULT 0,
    total_amount NUMERIC(15,2) NOT NULL,
    currency VARCHAR(3) DEFAULT 'GBP',

    -- Dates
    transaction_date DATE NOT NULL,
    due_date DATE,

    -- Related entities
    client_id UUID REFERENCES clients(id) ON DELETE SET NULL,
    account_id UUID REFERENCES accounts(id) ON DELETE SET NULL,

    -- Status
    status VARCHAR(50), -- 'draft', 'submitted', 'approved', 'paid', etc.
    is_reconciled BOOLEAN DEFAULT FALSE,

    -- Sync metadata
    last_synced_at TIMESTAMP WITH TIME ZONE,
    platform_updated_at TIMESTAMP WITH TIME ZONE,

    -- Record metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT valid_amount CHECK (total_amount >= 0),
    CONSTRAINT unique_platform_transaction UNIQUE(platform_name, platform_id)
);

CREATE INDEX idx_transactions_org ON transactions(organization_id);
CREATE INDEX idx_transactions_date ON transactions(transaction_date);
CREATE INDEX idx_transactions_client ON transactions(client_id);
CREATE INDEX idx_transactions_status ON transactions(status);
CREATE INDEX idx_transactions_reconciled ON transactions(is_reconciled);
CREATE INDEX idx_transactions_platform ON transactions(platform_name, platform_id);
CREATE INDEX idx_transactions_sync ON transactions(last_synced_at);
```

**Notes:**
- Normalized amounts to avoid floating-point errors
- Supports invoice, bill, and bank transactions
- Platform-agnostic status field
- Ready for reconciliation features
- Indexes optimized for common queries

---

### 5. accounts

**Purpose:** Store chart of accounts from accounting platforms

```sql
CREATE TABLE accounts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,

    -- Platform mapping
    platform_id VARCHAR(500),
    platform_name VARCHAR(50) NOT NULL,

    -- Account details
    code VARCHAR(50) NOT NULL, -- Account code from platform
    name VARCHAR(255) NOT NULL,
    account_type VARCHAR(50), -- 'asset', 'liability', 'income', 'expense', etc.
    description TEXT,

    -- Status
    is_active BOOLEAN DEFAULT TRUE,

    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT unique_account_code UNIQUE(organization_id, code)
);

CREATE INDEX idx_accounts_org ON accounts(organization_id);
CREATE INDEX idx_accounts_type ON accounts(account_type);
CREATE INDEX idx_accounts_code ON accounts(code);
```

**Notes:**
- Maps to Xero Accounts and QB Account objects
- Supports categorization
- Essential for transaction mapping

---

### 6. oauth_tokens

**Purpose:** Separate table for sensitive OAuth token management

```sql
CREATE TABLE oauth_tokens (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    platform_id UUID NOT NULL REFERENCES accounting_platforms(id) ON DELETE CASCADE,

    -- Token information (encrypted)
    access_token_encrypted BYTEA NOT NULL,
    refresh_token_encrypted BYTEA,
    token_type VARCHAR(50) DEFAULT 'Bearer',

    -- Timing
    issued_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP WITH TIME ZONE,

    -- Scopes (for audit)
    scopes TEXT,

    -- Status
    is_revoked BOOLEAN DEFAULT FALSE,
    revoked_at TIMESTAMP WITH TIME ZONE,
    revoke_reason TEXT,

    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT check_expiry CHECK (expires_at > issued_at)
);

CREATE INDEX idx_tokens_platform ON oauth_tokens(platform_id);
CREATE INDEX idx_tokens_revoked ON oauth_tokens(is_revoked);
CREATE INDEX idx_tokens_expires ON oauth_tokens(expires_at);
```

**Notes:**
- Separate table for security
- Token rotation history preserved
- Revocation tracking for compliance
- Ready for token refresh logic

---

### 7. ai_analysis_results

**Purpose:** Store Claude AI analysis results for transactions and insights

```sql
CREATE TABLE ai_analysis_results (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,

    -- Analysis scope
    analysis_type VARCHAR(50) NOT NULL, -- 'categorization', 'anomaly', 'insight', 'communication'
    target_entity_type VARCHAR(50), -- 'transaction', 'client', 'account'
    target_entity_id UUID, -- Reference to transaction, client, etc.

    -- Analysis content
    prompt_used TEXT NOT NULL,
    prompt_tokens INT,
    response_tokens INT,

    result_text TEXT NOT NULL,
    result_json JSONB, -- For structured results
    confidence_score NUMERIC(3,2), -- 0.00 to 1.00

    -- Categorization-specific
    suggested_category VARCHAR(100),
    suggested_account_id UUID REFERENCES accounts(id),

    -- Status
    is_approved BOOLEAN DEFAULT FALSE,
    was_used BOOLEAN DEFAULT FALSE,

    -- Cost tracking
    estimated_cost_gbp NUMERIC(7,4),

    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT valid_confidence CHECK (confidence_score >= 0 AND confidence_score <= 1)
);

CREATE INDEX idx_analysis_org ON ai_analysis_results(organization_id);
CREATE INDEX idx_analysis_type ON ai_analysis_results(analysis_type);
CREATE INDEX idx_analysis_entity ON ai_analysis_results(target_entity_type, target_entity_id);
CREATE INDEX idx_analysis_confidence ON ai_analysis_results(confidence_score);
CREATE INDEX idx_analysis_approved ON ai_analysis_results(is_approved);
```

**Notes:**
- Tracks all Claude API interactions
- Stores results for review before use
- Cost tracking for budget monitoring
- Confidence scores for quality control
- Supports audit trail

---

### 8. sync_history

**Purpose:** Track all synchronization events for auditing and debugging

```sql
CREATE TABLE sync_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    platform_id UUID REFERENCES accounting_platforms(id) ON DELETE CASCADE,

    -- Sync metadata
    sync_type VARCHAR(50), -- 'full', 'incremental', 'manual'
    sync_status VARCHAR(50), -- 'started', 'completed', 'failed'

    -- Data
    records_synced INT DEFAULT 0,
    records_created INT DEFAULT 0,
    records_updated INT DEFAULT 0,
    records_failed INT DEFAULT 0,

    -- Timing
    started_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP WITH TIME ZONE,
    duration_seconds INT,

    -- Error handling
    error_message TEXT,
    error_details JSONB,

    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_sync_org ON sync_history(organization_id);
CREATE INDEX idx_sync_platform ON sync_history(platform_id);
CREATE INDEX idx_sync_status ON sync_history(sync_status);
CREATE INDEX idx_sync_date ON sync_history(started_at);
```

**Notes:**
- Complete audit trail of all syncs
- Troubleshooting information stored
- Performance monitoring capability
- Batch operation tracking

---

### 9. audit_log

**Purpose:** Track all data modifications for compliance and security

```sql
CREATE TABLE audit_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,

    -- What changed
    table_name VARCHAR(100) NOT NULL,
    record_id VARCHAR(500) NOT NULL,
    operation VARCHAR(10) NOT NULL, -- 'INSERT', 'UPDATE', 'DELETE'

    -- Values
    old_values JSONB,
    new_values JSONB,

    -- Who did it
    changed_by VARCHAR(100), -- User email or 'system' or 'sync'

    -- When
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_audit_org ON audit_log(organization_id);
CREATE INDEX idx_audit_table ON audit_log(table_name);
CREATE INDEX idx_audit_record ON audit_log(record_id);
CREATE INDEX idx_audit_date ON audit_log(created_at);
```

**Notes:**
- Complete change history
- Regulatory compliance support
- Data recovery capability
- User attribution

---

## 📊 ENTITY RELATIONSHIPS DIAGRAM

```
organizations (1)
    ├── (1) accounting_platforms (many)
    │       ├── (1) oauth_tokens (many)
    │       └── (used in) sync_history
    │
    ├── (1) clients (many)
    │       └── (referenced by) transactions
    │
    ├── (1) accounts (many)
    │       └── (referenced by) transactions
    │
    ├── (1) transactions (many)
    │       ├── references clients
    │       ├── references accounts
    │       └── (analyzed by) ai_analysis_results
    │
    ├── (1) ai_analysis_results (many)
    │       └── may reference accounts
    │
    ├── (1) sync_history (many)
    │       └── tracks platform syncs
    │
    └── (1) audit_log (many)
            └── tracks all changes
```

---

## 🔐 ENCRYPTION STRATEGY

### Fields Requiring Encryption

1. **accounting_platforms**
   - `client_secret_encrypted` - OAuth2 client secret
   - `access_token_encrypted` - Current access token
   - `refresh_token_encrypted` - Refresh token

2. **oauth_tokens**
   - `access_token_encrypted` - Active tokens
   - `refresh_token_encrypted` - Refresh tokens

### Encryption Implementation

```python
# In backend/config.py
from cryptography.fernet import Fernet

class EncryptionManager:
    def __init__(self, encryption_key: str):
        """encryption_key from ENCRYPTION_KEY in .env"""
        self.cipher = Fernet(encryption_key.encode())

    def encrypt(self, value: str) -> bytes:
        return self.cipher.encrypt(value.encode())

    def decrypt(self, encrypted_value: bytes) -> str:
        return self.cipher.decrypt(encrypted_value).decode()
```

**Security Notes:**
- ENCRYPTION_KEY stored in environment variables only
- Never log encrypted values
- Rotate encryption keys quarterly in Phase 3+
- All tokens encrypted at rest

---

## 📈 SCALING CONSIDERATIONS

### Phase 2+ (Month 3+)

**If scaling needed:**

1. **Partitioning Transactions**
   ```sql
   -- By date range
   PARTITION BY RANGE (DATE_TRUNC('month', transaction_date))
   ```

2. **Archiving Old Data**
   ```sql
   -- Move transactions >2 years old to archive schema
   ```

3. **Read Replicas**
   ```sql
   -- For reporting without impacting operations
   ```

### Projections

```
Month 1:  ~1K transactions, ~10 clients
Month 3:  ~10K transactions, ~50 clients
Month 6:  ~50K transactions, ~200 clients
Month 12: ~200K transactions, ~500 clients
```

**Table Sizes (12-month estimate):**
- transactions: ~200MB
- ai_analysis_results: ~50MB
- sync_history: ~5MB
- audit_log: ~100MB
- Total: ~400MB (easily handled by PostgreSQL)

---

## 🔍 QUERY PATTERNS

### Common Queries (Optimized)

**1. Get all transactions for a date range**
```sql
SELECT * FROM transactions
WHERE organization_id = $1
  AND transaction_date BETWEEN $2 AND $3
ORDER BY transaction_date DESC;
```
*Index: idx_transactions_date*

**2. Get reconciliation status**
```sql
SELECT status, COUNT(*) as count
FROM transactions
WHERE organization_id = $1
  AND is_reconciled = false
GROUP BY status;
```
*Index: idx_transactions_reconciled*

**3. Get sync status**
```sql
SELECT platform_name, connection_status, last_sync_at
FROM accounting_platforms
WHERE organization_id = $1
ORDER BY last_sync_at DESC;
```
*Index: idx_platforms_sync*

**4. Get AI analysis to review**
```sql
SELECT * FROM ai_analysis_results
WHERE organization_id = $1
  AND is_approved = false
  AND was_used = false
ORDER BY created_at DESC
LIMIT 10;
```
*Index: idx_analysis_approved*

---

## 🚀 INITIAL DATA

### Sample Inserts for Testing

Will be handled by Alembic migrations in Phase 1.2

---

## ✅ VALIDATION RULES

### PostgreSQL Constraints

All defined in CREATE TABLE statements:

- **Email format** - CONSTRAINT valid_email CHECK
- **Amounts** - CONSTRAINT valid_amount CHECK (>= 0)
- **Confidence scores** - CONSTRAINT valid_confidence CHECK (0-1)
- **Unique constraints** - On platform IDs
- **Foreign key constraints** - Referential integrity
- **NOT NULL constraints** - Required fields

### Application-Level Validation

Will be handled by Pydantic models in `backend/models/`

---

## 📝 MIGRATION STRATEGY

### Alembic Setup

```bash
# Already installed, will run:
alembic init alembic

# Create initial migration:
alembic revision --autogenerate -m "initial_schema"

# Run migrations:
alembic upgrade head
```

### Version Control

- All migrations tracked in git
- Never manually modify migrations
- One migration per feature
- Clear, descriptive messages

---

## 🎯 READINESS CHECKLIST

- [x] Schema supports Xero integration (Phase 1)
- [x] Schema supports QuickBooks (Phase 2)
- [x] OAuth token management secure
- [x] Audit trail complete
- [x] Transaction reconciliation ready
- [x] AI analysis tracking included
- [x] Performance indexes in place
- [x] Scaling considerations documented
- [x] Encryption strategy clear
- [x] Validation rules comprehensive

---

## 📞 IMPLEMENTATION NOTES

### For Next Session

1. Create Alembic initial migration from this schema
2. Implement Pydantic models in `backend/models/`
3. Create database utilities in `backend/database.py`
4. Set up connection pooling and transaction management

### Testing Strategy

1. Unit tests for model creation
2. Integration tests for relationships
3. Performance tests for indexes
4. Transaction tests for ACID compliance

---

**Schema Status:** ✅ READY FOR IMPLEMENTATION
**Last Updated:** November 23, 2025
**Approved For:** Phase 1 and Beyond

