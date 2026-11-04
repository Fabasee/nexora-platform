# Nexora Security Event Center

## API

Authenticated users can retrieve their own latest security events:

`GET /api/v1/account/security-events/`

The endpoint returns at most 50 events, newest first. The query is always scoped to the authenticated internal Nexora UUID. It never accepts a user ID from the client.

Current event:
- `identity.authenticated`: a Firebase ID token was successfully verified by the API.

Authentication events are deduplicated by the canonical user UUID, provider, and Firebase `auth_time`. This avoids incorrectly recording every API request as a separate login.

## Data minimization

Stored fields:
- Internal user UUID
- Event type and server-recorded timestamp
- Identity provider name
- Direct remote IP address when supplied by the application server
- User-Agent (truncated to 512 characters)
- Optional request correlation ID (truncated to 128 characters)
- Internal deduplication hash

Never store:
- Firebase ID tokens, refresh tokens, passwords, authorization headers, or request bodies
- Firebase provider subjects in the event record
- Client-supplied role, plan, or permission claims

The API does not trust `X-Forwarded-For` for source IP attribution. Configure trusted proxy handling explicitly before relying on IP addresses behind a reverse proxy.

## Integrity and access

- Events are append-only through the Django admin: staff can inspect but cannot add, edit, or delete them.
- Users can see only events associated with their own authenticated Nexora UUID.
- The event model uses `PROTECT` on its user relation.
- Production database permissions, backups, and retention controls must also protect audit records.

## Production hardening still required

1. Define and implement a retention period aligned with applicable privacy requirements.
2. Add alerting for suspicious authentication patterns and repeated failures.
3. Record failed authentication without storing raw tokens or untrusted identity subjects.
4. Configure trusted proxy IP extraction and request-ID generation at the edge.
5. Consider exporting high-value events to a separate append-only log sink.
6. Add event coverage for verification requests, credential changes, recovery, and session revocation as those flows are implemented.

This is an initial security audit foundation, not a complete SIEM or fraud-detection system.
