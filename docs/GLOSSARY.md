# Glossary & Naming Conventions

**Purpose**: Canonical definitions for all team members. Use these terms consistently in code, comments, documentation, and conversation.

**Rule**: If a term isn't here, add it before using it in code.

---

## 1. Domain Model Terms

### Organization
- **What**: The SaaS tenant. An accounting practice or firm using our software.
- **Examples**: "Smith & Co Accountants", "ABC Bookkeeping Ltd"
- **DB Table**: `organizations`
- **Code**: `Organization` model
- **RLS**: All tenant isolation is scoped to `organization_id`

**NOT**: The end-client's business. That's a "Client".

---

### User
- **What**: A person with login credentials. Belongs to an Organization.
- **Examples**: An accountant, bookkeeper, manager, or admin at the practice
- **DB Table**: `users`
- **Code**: `User` model
- **Key fields**: `email`, `organization_id`, `role`

**NOT**: The client's employees. We don't model those.

---

### Client
- **What**: A customer/counterparty of an Organization. A business being managed.
- **Examples**: "The Red Lion Pub", "ABC Manufacturing Ltd"
- **DB Table**: `clients`
- **Code**: `Client` model
- **Key fields**: `organization_id`, `platform_id`, `platform_name`

**NOT**: A user of our software. That's a "User".

---

### Account
- **What**: A chart-of-accounts entry. **Client-scoped**, not organization-scoped.
- **Examples**: "Sales Income (200)", "Cost of Goods Sold (4000)"
- **DB Table**: `accounts`
- **Code**: `Account` model
- **Key fields**: `client_id`, `code`, `platform_id`
- **Uniqueness**: `(client_id, code)` - each client has independent CoA

**NOT**: A user account (that's "User"). **NOT** organization-level (each client has their own).

---

### ClientAssignment
- **What**: A workflow assignment linking a User to a Client.
- **Purpose**: Track responsibility, not access control. All users can access all clients in their org.
- **DB Table**: `client_assignments`
- **Code**: `ClientAssignment` model
- **Roles**: `primary`, `accountant`, `reviewer`, `backup`

**NOT**: Access control. RLS handles that at org level.

---

### Transaction
- **What**: A financial transaction (invoice, bill, payment, etc.)
- **DB Table**: `transactions`
- **Code**: `Transaction` model
- **Key fields**: `client_id`, `organization_id`, `platform_id`

---

### Accounting Platform
- **What**: An external provider connection (Xero, QuickBooks, FreeAgent, etc.)
- **DB Table**: `accounting_platforms`
- **Code**: `AccountingPlatform` model
- **Key fields**: `organization_id`, `platform_name`

---

### Platform ID
- **What**: A stable external identifier from a provider (Xero ContactID, QB Id, etc.)
- **Rule**: Must be idempotency-safe. If it changes between syncs, don't call it `platform_id`.
- **Column**: `platform_id` (on clients, transactions, accounts)

---

## 2. Data Architecture Terms

### Raw Layer
- **What**: Upstream data stored faithfully, no interpretation
- **Tables**: `transactions`, `clients`, `accounts` (with `source_payload`)
- **Rule**: Never report directly from raw. Always go through mapping.

### Mapping Layer
- **What**: Translates platform-specific meaning to system meaning
- **Tables**: `platform_transaction_mapping`
- **Output**: `normalized_type`, `normalized_status`, `canonical_bucket`

### Canonical Facts
- **What**: Single source of truth for reporting and AI
- **Tables**: `cashflow_facts_v1`
- **Rule**: Reports read facts only. Never join to raw.

### Quarantine
- **What**: Rows that couldn't be mapped. Excluded from reports.
- **Table**: `ingestion_quarantine`
- **Rule**: Quarantine is a feature, not a failure.

---

## 3. Security Terms

### RLS (Row-Level Security)
- **What**: PostgreSQL feature enforcing tenant isolation at DB level
- **Scope**: `organization_id` on all tenant tables
- **Context**: Set via `SET app.org_id = '<uuid>'` before queries

### FORCE RLS
- **What**: RLS applies even to table owner
- **Applied to**: Most tenant tables
- **Exceptions**: `users`, `organizations` (auth/registration needs bypass)

### Composite FK
- **What**: Foreign key on multiple columns enforcing cross-table consistency
- **Example**: `(organization_id, client_id) → clients(organization_id, id)`
- **Purpose**: Prevents cross-org references even if application bugs

---

## 4. Naming Conventions

### Database Tables
| Convention | Example |
|------------|---------|
| Lowercase snake_case | `client_assignments` |
| Plural nouns | `users`, `clients`, `transactions` |
| Junction tables: `<entity1>_<entity2>s` | `client_assignments` |

### Database Columns
| Convention | Example |
|------------|---------|
| Lowercase snake_case | `organization_id`, `created_at` |
| Foreign keys: `<entity>_id` | `client_id`, `user_id` |
| Timestamps: `<action>_at` | `created_at`, `updated_at`, `assigned_at` |
| Booleans: `is_<state>` | `is_active`, `is_admin` |
| Platform refs: `platform_<field>` | `platform_id`, `platform_name` |

### Database Constraints
| Type | Pattern | Example |
|------|---------|---------|
| Primary key | `<table>_pkey` | `clients_pkey` |
| Foreign key | `fk_<table>_<target>` | `fk_client_assignments_client` |
| Unique | `uq_<table>_<columns>` | `uq_clients_org_id` |
| Check | `ck_<table>_<field>` | `ck_client_assignments_role` |
| Index | `ix_<table>_<columns>` | `ix_client_assignments_user_active` |

### Database Policies (RLS)
| Pattern | Example |
|---------|---------|
| `p_<table>_<purpose>` | `p_client_assignments_tenant_isolation` |

### Database Triggers
| Pattern | Example |
|---------|---------|
| `set_<field>_<table>` | `set_updated_at_client_assignments` |

---

## 5. Code Conventions

### Python Files
| Convention | Example |
|------------|---------|
| Lowercase snake_case | `client_assignment.py` |
| Models: singular noun | `client.py`, `user.py` |
| Routes: `<entity>_routes.py` | `documents_routes.py` |
| Services: `<purpose>.py` | `claude_ocr.py` |

### Python Classes
| Convention | Example |
|------------|---------|
| PascalCase | `ClientAssignment`, `DocumentDraft` |
| Models: singular noun | `Client`, `User`, `Account` |
| Services: `<Purpose>Service` | `ClaudeOCRService` |

### Python Constants
| Convention | Example |
|------------|---------|
| UPPER_SNAKE_CASE | `ASSIGNMENT_ROLES`, `SUPPORTED_MIME_TYPES` |

### API Endpoints
| Convention | Example |
|------------|---------|
| Lowercase kebab-case | `/api/client-assignments` |
| Resource plural | `/api/clients`, `/api/users` |
| Actions as verbs | `/api/inbox/{id}/extract` |

---

## 6. Comment Standards

### Required Comments

**Tables** (via SQL COMMENT):
```sql
COMMENT ON TABLE client_assignments IS
'User-to-client workflow assignments. NOT access control.';
```

**Complex constraints**:
```sql
COMMENT ON CONSTRAINT fk_client_assignments_client ON client_assignments IS
'Composite FK ensures client belongs to same organization.';
```

**Non-obvious code**:
```python
# Composite FK enforces same-org at DB level, but we check here too
# for clearer error messages before hitting the constraint
if client.organization_id != current_user.organization_id:
    raise ValueError("Client belongs to different organization")
```

### When NOT to Comment
- Self-explanatory code: `user.is_active = False`
- Standard patterns: `created_at = Column(DateTime, default=func.now())`

---

## 7. Versioning

### Migration IDs
| Pattern | Example |
|---------|---------|
| `v2_<sequence>_<description>` | `v2_095_client_assignments` |

### Sequences in Use
| Range | Purpose |
|-------|---------|
| v2_001-v2_050 | Database hardening (Phase 4A) |
| v2_051-v2_070 | Canonical mapping layer |
| v2_071-v2_079 | Cashflow facts |
| v2_080-v2_089 | Document review |
| v2_090-v2_099 | RLS and auth |
| v2_100+ | Future |

---

## 8. Abbreviations

| Abbreviation | Meaning | Use |
|--------------|---------|-----|
| org | Organization | Variables only, never in schema |
| CoA | Chart of Accounts | Documentation only |
| FK | Foreign Key | Documentation only |
| RLS | Row-Level Security | Everywhere |
| PK | Primary Key | Documentation only |
| UUID | Universally Unique Identifier | Everywhere |

**Rule**: Don't abbreviate in table/column names. `organization_id` not `org_id` (except legacy).

---

## 9. Anti-Patterns (Don't Do This)

| Don't | Do Instead |
|-------|------------|
| `org_id` in new tables | `organization_id` |
| Free-text role columns | CHECK constraints or lookup tables |
| Single-column FKs for cross-table consistency | Composite FKs |
| `account` (ambiguous) | `chart_account` or context-specific |
| Comments explaining what | Comments explaining why |
| `getUserClients()` | `getClientsForUser()` or `user.clients` |

---

## 10. Adding to This Document

When you introduce a new term:

1. Add it to the appropriate section
2. Include: What it is, what it's NOT, DB table, code class
3. Commit with message: `docs: Add <term> to glossary`

**No undocumented domain terms in code.**

---

**Last Updated**: February 3, 2026
**Maintainer**: Engineering Team
