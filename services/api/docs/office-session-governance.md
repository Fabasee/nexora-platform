# Nexora Office Session & Device Governance

## Access control
All routes require an active staff account, a Firebase-verified email claim, and the `sessions.manage` Office permission. The permission is granted to Office Owner and Office Security Admin only.

## Routes
- `GET /api/v1/office/access/sessions/` — paginated session inventory; optional `user_id` UUID and `active=true|false` filters. Maximum page size is 100.
- `POST /api/v1/office/access/sessions/{session_id}/revoke/` — revoke one session.
- `POST /api/v1/office/access/users/{user_id}/sessions/revoke/` — revoke all active sessions for one account, except the operator's current session to prevent accidental lockout.

## Audit and privacy
Session revocations create `identity.session_revoked` security events. `user` identifies the account whose session was revoked; `actor` identifies the authenticated operator. Existing events remain valid with a null actor. The inventory exposes provider, timestamps, MFA state, source IP and user-agent string; it does not expose provider subjects, Firebase tokens, credentials, or request bodies.

IP address and user-agent are diagnostic metadata, not proof of a person's identity or precise location. No geolocation lookup is performed. Device/browser labels should be derived client-side from the user-agent and treated as approximate.

## Operational note
Run `python manage.py migrate` to add the nullable security-event actor relation. The existing account-scoped session endpoints remain unchanged.
