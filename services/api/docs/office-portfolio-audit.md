# Nexora Office Portfolio Audit

The portfolio audit log records changes made through the Django Admin and the
version-controlled manifest synchronization command.

## API

`GET /api/v1/office/audit/`

Requires the same staff authorization and server-verified email checks as the
Office portfolio endpoints.

Query parameters:
- `entry_key`: exact portfolio key
- `action`: `created` or `updated`
- `source`: `admin` or `manifest`
- `limit`: defaults to 50 and is capped at 100
- `offset`: defaults to 0

Each event includes the entry key/name snapshot, action, source, actor label,
field-level before/after values, and timestamp. Secrets and account credentials
are not part of the portfolio schema and are never copied into this audit log.

## Write paths

- Django Admin calls `save_portfolio_entry` with the authenticated staff user.
- `sync_product_registry` calls the same service with source `manifest`.
- The portfolio row and audit event are written in one database transaction.
- No-op manifest syncs do not generate audit noise.
- Portfolio deletion is disabled in Django Admin; the registry sync remains
  non-destructive.
- Audit records are read-only in Django Admin and reject model-level update and
  delete operations through the application model.

## Integrity boundary

This is an append-only application-level audit log, not a cryptographically
tamper-proof ledger. A database owner or privileged SQL operator can still
alter underlying rows. Production hardening should add database permissions or
triggers, centralized log export, retention controls, and optionally signed
event chaining before the audit log is used as a compliance-grade record.
