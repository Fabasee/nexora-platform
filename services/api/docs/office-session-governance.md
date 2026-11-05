# Nexora Office Session & Device Governance

## Access control
All routes require an active staff account, a Firebase-verified email claim, and the `sessions.manage` Office permission. The permission is granted to Office Owner and Office Security Admin only.

## Routes
- `GET /api/v1/office/access/sessions/` — paginated session inventory; optional `user_id` UUID and `active=true|false` filters. Maximum page size is 100.
- `POST /api/v1/office/access/sessions/{session_id}/revoke/` — revoke one session.
- `POST /api/v1/office/access/users/{user_id}/sessions/revoke/` — revoke all active sessions for one account, except the operator's current session to prevent accidental lockout.

## Audit and privacy
Session revocations create `identity.session_revoked` security events. `user` identifies the account whose session was revoked; `actor` identifies the authenticated operator. Events without a deduplication key are always appended; events with a stable deduplication key are idempotent. Inventory exposes provider, timestamps, MFA state, source IP and user-agent string; it does not expose provider subjects, Firebase tokens, credentials, or request bodies.

IP address and user-agent are diagnostic metadata, not proof of a person's identity or precise location. No geolocation lookup is performed. Device/browser labels derived client-side from user-agent are approximate.

## Revocation behavior
A revoked Nexora session is rejected by the API authentication layer on subsequent requests, in addition to Firebase token revocation checks. Revocation is idempotent; a repeated single-session revoke reports `already_revoked`. Bulk revocation preserves the operator's current session when the request carries its server-resolved session ID.

## Operational note
Run `python manage.py migrate` before deploying the nullable security-event actor relation. Protect Django Admin and production credentials with MFA, network restrictions, secure backups, and monitored privileged access.
