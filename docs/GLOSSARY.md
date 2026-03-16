# Glossary & Domain Canon

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

### Contact
- **What**: A vendor, customer, or supplier that a Client transacts with. The counterparty on bills and sales invoices.
- **Examples**: "Crouchers Orchards" (vendor sending a bill to a Client), "Smith & Partners LLP" (customer of a Client)
- **DB Table**: `contacts`
- **Code**: `Contact` model
- **Key fields**: `client_id`, `organization_id`, `name`, `contact_type`
- **Contact Types**: `vendor` (AP), `customer` (AR), `both` (AP+AR)
- **Purpose**: Fuzzy matching during OCR extraction, sync with accounting software contact databases

**AP/AR Direction**:
| `contact_type` | Ledger | Meaning | They appear on... |
|---|---|---|---|
| `vendor` | **Accounts Payable (AP)** | They send us bills, we pay them | Bills, purchase orders |
| `customer` | **Accounts Receivable (AR)** | We send them sales invoices, they pay us | Sales invoices, estimates |
| `both` | **AP + AR** | Trades in both directions | Either document type |

**Platform Term Mapping** (our canonical `contact_type` maps to each platform's terminology):
| Our Term | Xero | QuickBooks | FreeAgent | Sage |
|---|---|---|---|---|
| `vendor` | Contact (supplier) | Vendor | Supplier | Supplier |
| `customer` | Contact (customer) | Customer | Client | Customer |
| `both` | Contact (both) | — | — | — |

**Domain Model Hierarchy**:
```
Organization (accounting firm)
└── Client (business whose books we manage)
    └── Contact (vendors/customers that Client deals with)
        ├── vendor (AP) → appears on bills
        └── customer (AR) → appears on sales invoices
```

**NOT**: The Client itself. A Client is our customer (the business we manage). A Contact is THEIR customer or vendor.

**NOT**: "Vendor" or "Supplier" in isolation - use "Contact" as the canonical term since it can be either vendor OR customer. The `contact_type` field distinguishes direction.

---

### Transaction
- **What**: A financial transaction (bill, sales invoice, payment, etc.)
- **DB Table**: `transactions`
- **Code**: `Transaction` model
- **Key fields**: `client_id`, `organization_id`, `platform_id`

---

## 1b. Canonical Document Types

The word "invoice" is **ambiguous** in common usage - it could mean a bill (AP) or a sales invoice (AR). We resolve this by never using the bare word "invoice" in code or API. Every document type has an explicit AP/AR direction.

**Rule**: Always use the canonical term in code, database columns, API fields, and conversation. If someone says "invoice", ask: "AP or AR?"

### AP Documents (Accounts Payable - we owe money)

| Canonical Term | Code Enum | What It Is | Contact Direction |
|---|---|---|---|
| `bill` | `BILL` | A vendor sent this to our Client. Client owes vendor money. | vendor (AP) |
| `credit_note_received` | `CREDIT_NOTE_RECEIVED` | A vendor credited our Client. Reduces amount owed. | vendor (AP) |
| `purchase_order` | `PURCHASE_ORDER` | An order our Client sent to a vendor. Pre-purchase. | vendor (AP) |
| `payment_made` | `PAYMENT_MADE` | Our Client paid a vendor. Settles a bill. | vendor (AP) |

### AR Documents (Accounts Receivable - money owed to us)

| Canonical Term | Code Enum | What It Is | Contact Direction |
|---|---|---|---|
| `sales_invoice` | `SALES_INVOICE` | Our Client sent this to a customer. Customer owes Client money. | customer (AR) |
| `credit_note_issued` | `CREDIT_NOTE_ISSUED` | Our Client credited a customer. Reduces amount they owe. | customer (AR) |
| `estimate` | `ESTIMATE` | A quote our Client sent to a customer. Pre-sale. | customer (AR) |
| `payment_received` | `PAYMENT_RECEIVED` | A customer paid our Client. Settles a sales invoice. | customer (AR) |

### Platform Document Type Mapping

Each accounting platform uses different names for the same concepts. Our mapping layer translates to canonical terms.

| Our Canonical Term | Xero | QuickBooks | FreeAgent | Sage |
|---|---|---|---|---|
| `bill` | Bill | Bill | Bill | Purchase Invoice |
| `sales_invoice` | Invoice | Invoice | Invoice | Sales Invoice |
| `credit_note_received` | Credit Note (from contact) | Vendor Credit | — | Purchase Credit Note |
| `credit_note_issued` | Credit Note (to contact) | Credit Memo | — | Sales Credit Note |
| `estimate` | Quote | Estimate | Estimate | Quotation |
| `purchase_order` | Purchase Order | Purchase Order | — | Purchase Order |
| `payment_made` | Payment (spend) | Bill Payment | — | Purchase Payment |
| `payment_received` | Payment (receive) | Payment | — | Sales Receipt |

### Document Type Determination from OCR

When the AI extracts a document, the document type can usually be inferred from:
1. **Document header text**: "INVOICE", "BILL", "CREDIT NOTE", "ESTIMATE", "QUOTE"
2. **Contact direction**: If the contact is a `vendor`, the document is likely AP (bill). If `customer`, likely AR (sales_invoice).
3. **Our Client's position**: Is our Client the buyer or the seller on this document?

**Key rule**: If OCR detects "INVOICE" in the header, check the contact direction to determine if it's a `bill` (AP) or `sales_invoice` (AR). Never store the bare type "invoice".

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
- **Applied to**: All tenant tables including `users` and `organizations`
- **Auth Bypass**: Via SECURITY DEFINER functions only (not table ownership)

### SECURITY DEFINER
- **What**: PostgreSQL function attribute that runs with owner's privileges
- **Purpose**: Provides controlled RLS bypass for specific operations
- **Applied to**: `auth_lookup_user_by_email`, `auth_lookup_org_by_id`, `auth_create_pending_user`, `auth_activate_user`
- **Owner**: `auth_definer` role (dedicated, NOLOGIN)
- **Hardening**: `SET search_path = pg_catalog, public`, minimal return fields

### auth_definer Role
- **What**: Dedicated PostgreSQL role that owns SECURITY DEFINER auth functions
- **Properties**: NOLOGIN (cannot be used for connections)
- **Privileges**: SELECT on users and organizations only
- **Purpose**: Explicit, auditable bypass surface for auth operations

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
| v2_100-v2_114 | DB hardening v2 (FINAL_NON_NEGOTIABLE) |
| v2_115-v2_116 | Client-scoped documents + contacts |
| v2_117+ | Future |

### Key Migrations (v2_110-v2_114)
| Migration | Description |
|-----------|-------------|
| v2_095 | client_assignments table with composite FKs |
| v2_110 | accounts.client_id NOT NULL + composite FK + idempotency |
| v2_111 | accounting_platforms: oauth_client_id + managed_client_id |
| v2_112 | users pending invariant + CHECK constraints |
| v2_113 | Case-insensitive email uniqueness |
| v2_114 | SECURITY DEFINER auth functions + FORCE RLS |
| v2_115 | client_id on document_inbox_item + document_draft |
| v2_116 | contacts table with RLS + composite FKs |

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
| AP | Accounts Payable | Everywhere - money our Client owes to vendors |
| AR | Accounts Receivable | Everywhere - money owed to our Client by customers |

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
| `invoice` (ambiguous - AP or AR?) | `bill` (AP) or `sales_invoice` (AR) |
| `type = "invoice"` in code/DB | `document_type = "bill"` or `document_type = "sales_invoice"` |
| `credit_note` (ambiguous direction) | `credit_note_received` (AP) or `credit_note_issued` (AR) |
| `payment` (ambiguous direction) | `payment_made` (AP) or `payment_received` (AR) |
| `vendor` as a model name | `Contact` with `contact_type = "vendor"` |
| `supplier` in code | `Contact` with `contact_type = "vendor"` |

---

## 10. Adding to This Document

When you introduce a new term:

1. Add it to the appropriate section
2. Include: What it is, what it's NOT, DB table, code class
3. Commit with message: `docs: Add <term> to glossary`

**No undocumented domain terms in code.**

---

**Last Updated**: February 5, 2026
**Maintainer**: Engineering Team

---

## Foundational Concepts (Canonical)

**Tenant Boundary**  
The database enforces tenancy at the **organization** level. No row belonging to one organization may be visible to, or referenced by, another organization unless explicitly designed and documented.  
This is enforced structurally (Row-Level Security + constraints), not by application convention.

**External Realm**  
An external realm is the scope within which an external provider’s identifiers are guaranteed to be unique (e.g. a Xero tenant or a QuickBooks company).  
External IDs are **never assumed globally unique** unless explicitly proven by the provider.

**Idempotency**  
Idempotency means retrying the same external sync operation must not create duplicate records.  
Idempotency is enforced at the database level using uniqueness constraints, not application logic.

**Declarative Enforcement**  
Wherever possible, invariants are enforced using declarative database constraints (FOREIGN KEY, UNIQUE, CHECK).  
Triggers and application logic are secondary controls and must not be the sole enforcement mechanism.

---

## Core Domain Entities (Extended Definitions)

### Organization
**Definition:**  
The SaaS tenant. Represents an accounting practice or firm using the platform.

**Uniqueness:**  
Not globally unique by name.

**Scope:**  
Top-level tenant boundary. All Row-Level Security policies and cross-table integrity checks ultimately scope to `organization_id`.

**Notes:**  
An organization owns users and clients, but does **not** own a chart of accounts directly.

---

### User
**Definition:**  
A person with login credentials who performs actions on behalf of an organization.

**Uniqueness:**  
Email address is globally unique (case-insensitive).

**Lifecycle States:**  
- `pending`: no organization assigned yet  
- `active`: belongs to an organization  
- `suspended` / `disabled`: access revoked

**Notes:**  
A user must never be active without an `organization_id`. This invariant is enforced at the database level.

---

### Client
**Definition:**  
A business entity managed by an organization (the organization’s customer).

**Uniqueness:**  
Unique only within an organization.

**Scope:**  
Clients are children of an organization. All client-owned data must reference both `client_id` and `organization_id` consistently.

**Notes:**  
Each client may have its own independent external accounting system.

---

### Accounts
**Definition:**  
Client-scoped chart of accounts entries, typically synced from the client’s external accounting platform.

**Uniqueness:**  
- Account codes are unique per client.  
- External account identities are unique per client per external realm.

**Scope:**  
Accounts belong to exactly one client and one organization.

**Notes:**  
There is no organization-level chart of accounts. This is intentional and non-standard.

---

## External Integration Terminology

### Accounting Platform
**Definition:**  
A connection to an external accounting provider (e.g. Xero, QuickBooks) representing a single external realm.

**Scope:**  
Belongs to one organization and (in the target model) one client.

**Notes:**  
A single organization may manage many accounting platforms on behalf of different clients.

---

### platform_id
**Definition:**  
The external provider’s identifier for a specific object (account, transaction, etc.).

**Uniqueness Scope:**  
Unique only within the external realm (accounting platform).  
Never assumed unique across organizations or clients.

**Notes:**  
All uses of `platform_id` must be paired with an appropriate scoping key (`client_id` or `accounting_platform_id`).

---

### oauth_client_id
**Definition:**  
OAuth application identifier issued by an external provider.

**Notes:**  
This is **not** a reference to a business client. The name exists to prevent semantic confusion.

---

## NULL Semantics (Required Reading)

In this system, NULL values are not arbitrary. Each nullable field has defined semantics.

Examples:
- `users.organization_id`  
  - NULL only when `status = 'pending'`  
  - Forbidden otherwise

- `accounts.platform_id`  
  - NULL only for local/manual accounts (if supported)  
  - Non-NULL for synced accounts

- `accounting_platforms.managed_client_id`  
  - NULL only during transitional phases  
  - Target state: NOT NULL for all active connections

NULL must always mean one of:
- “not yet assigned (transitional)”
- “not applicable by design”

NULL must never mean “we didn’t get around to setting it”.

---

## Deferred Architectural Decisions

The following decisions are intentionally deferred and documented:

- **Assignment-based access control (RLS)**  
  All users in an organization can access all clients in that organization.  
  `client_assignments` track workflow responsibility, not permissions.  
  This is a product decision and may change for enterprise customers.

- **Fully client-scoped accounting_platforms**  
  Schema changes are in progress to support this.  
  During transition, constraints exist to prevent drift.

Deferred does not mean forgotten. Each item has explicit revisit criteria.

---

## Governance Rule

Any new database table, column, or constraint must be added to this glossary or explicitly reference an existing glossary term.  
If it cannot be clearly defined here, it should not exist in the schema.
