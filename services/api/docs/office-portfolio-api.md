# Nexora Office — Portfolio API

The internal portfolio API is separate from the consumer product catalog and account APIs.

## Access boundary

All routes require both:
- an authenticated Nexora identity with `is_staff=True`;
- a server-verified email claim on the current request.

Regular authenticated users cannot access these routes. The API is read-only in this phase; portfolio changes continue through Django Admin and the reviewed JSON registry sync workflow.

## Routes

- `GET /api/v1/office/summary/` — counts by entry type, lifecycle, decision status, and priority.
- `GET /api/v1/office/portfolio/` — paginated portfolio list.
- `GET /api/v1/office/portfolio/{key}/` — one entry with its direct modules.

List query parameters:
- `entry_type`: application, module, platform_service
- `lifecycle_status`: in_development, planned, research, proposed, live, paused
- `decision_status`: confirmed, candidate
- `priority`: core, viral, strategic, supporting, future
- `delivery_model`: standalone, module, shared
- `parent`: parent application key
- `search`: matches name, key, description, or category
- `limit`: 1–100 (default 50)
- `offset`: zero-based offset (default 0)

The portfolio API does not create runtime products, memberships, subscriptions, or entitlements. Those remain separate product-account lifecycle operations.


## Portfolio audit history

`GET /api/v1/office/audit/` returns the latest portfolio change events to
authorized Office staff. It supports exact `entry_key`, `action` (`created`
or `updated`), `source` (`admin` or `manifest`), and bounded
`limit`/`offset` pagination (maximum 100 records per request).

Each event includes the entry snapshot, actor label, source, timestamp, and
field-level before/after values. Audit events are written transactionally with
portfolio changes and are append-only at the application model/admin layer.
They are not yet cryptographically tamper-proof against privileged database
operators; see `office-portfolio-audit.md`.
