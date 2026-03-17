# Glossary

This glossary is the current domain canon for the client-centric document pipeline.

## Organization

The tenant. An accounting practice or firm using the platform.

- Table: `organizations`
- Scope key: `organization_id`

## User

A person with login credentials acting inside an organization.

- Table: `users`
- Scope key: `organization_id`

## Client

A business whose books an organization manages.

- Table: `clients`
- Scope key: `organization_id`

## Contact

A client-owned counterparty. Contacts represent the suppliers, vendors, or customers that appear on the client’s business documents.

- Table: `contacts`
- Scope keys: `organization_id`, `client_id`
- Important: contacts, not clients, are the counterparty entity used by client-specific suggestion logic

## Account

A client-scoped chart-of-accounts entry.

- Table: `accounts`
- Scope keys: `organization_id`, `client_id`

## Client-Centric Document Ingestion

The canonical document entry path. Every uploaded document must be associated with a client at intake time. There is no active generic or clientless AI ingestion route.

## Document Inbox Item

The canonical ingestion record for one uploaded document.

- Table: `document_inbox_item`
- Purpose: file metadata, checksum, client scope, and pipeline status

## OCR Result

Stored OCR/extraction evidence for an inbox item.

- Table: `document_ocr_result`
- Purpose: preserve raw text and extraction metadata

## Document Draft

The editable review object created from OCR output and interpretation.

- Table: `document_draft`
- Purpose: hold guessed values, confirmed values, validation output, draft JSON, and explicit confirmed-contact state

## OCR vs Interpretation

OCR extracts raw structure and text from the file. Interpretation turns that evidence into draft suggestions in client context. OCR is evidence; interpretation is advisory.

For counterparties in this subsystem:
- OCR supplier text is the extracted counterparty name from the document
- suggested contact is an advisory match from client-specific logic
- confirmed contact is the reviewer-selected client-scoped `Contact`

## Client Intelligence Layer

The additive, client-scoped memory layer used to improve review suggestions without bypassing review.

- Tables:
  - `client_intelligence_profile`
  - `client_supplier_alias`
  - `client_accounting_pattern`
  - `client_intelligence_event`
- Current state: schema exists, read-only lookup service exists, write-back is not implemented yet

## Client Intelligence Profile

One anchor record per client for intelligence state and metadata.

- Table: `client_intelligence_profile`
- Purpose: top-level client-scoped intelligence identity

## Client-Specific Suggestion Logic

Deterministic, explainable suggestion building that reads the client’s contacts, supplier aliases, and accounting patterns.

Current implemented behavior:
- exact normalized alias match from `client_supplier_alias`
- exact normalized contact-name fallback
- read-only pattern lookup from `client_accounting_pattern`
- explainable confidence tiers and reasons

## Suggestion Payload

The explainable advisory payload stored in `document_draft.draft_json["suggestions"]`.

Current sections:
- `contact`
- `nominal_account`
- `document_type`
- `tax_code`

Each section carries:
- suggested value or id
- confidence: `high`, `medium`, or `low`
- deterministic reasons

Suggestions remain separate from confirmed review values.

## Confirmed Contact

The canonical confirmed counterparty representation for document review and submit.

- Draft field: `document_draft.confirmed_contact_id`
- Scope: must resolve to a `contacts.id` row belonging to the same client
- Review payload: `confirmed_contact_id`
- Purpose: explicit reviewer confirmation, not OCR output and not suggestion output
- Legacy `counterparty_id` is not part of the canonical document-subsystem semantics

## Review Boundary

Suggestions do not confirm values automatically. Human review is still required before submission.

## Document Repository

A logical concept only at present. No `document_repository` table exists in the current repo state.

## Approved Document

A deferred concept for a future immutable reviewed snapshot. No approved-document table exists yet.

## Posting Boundary

The deterministic accounting conversion boundary after review. It remains to be finalized and is not redesigned in the current implementation pass.
