# Nexora identity sessions

## Session identity

A Nexora API session is anchored to a verified Firebase provider account and the token's server-verified `auth_time` claim. The client cannot choose another user's session or set its authentication timestamp.

This is intentionally not a device fingerprint. User-Agent and remote IP are informational metadata only; both can change and neither is trusted as proof of device identity.

## API

- `GET /api/v1/account/sessions/` — list up to 50 sessions belonging to the authenticated Nexora UUID.
- `POST /api/v1/account/sessions/{session_id}/revoke/` — revoke one session belonging to that same account.

The API never accepts a user UUID in these requests. Session ownership is enforced in the database query. A revoked session is rejected on its next API request even if Firebase still considers its ID token cryptographically valid.

The session list marks the current session based on the session resolved by the authentication layer. The mobile UI does not offer revocation of the current session; users can sign out instead.

## Authentication-context signals

When a new Firebase-authenticated Nexora session is created, Nexora compares available IP and User-Agent values with the immediately preceding session for the same provider account. If either available value differs, it records `identity.auth_context_changed` in the security-event history.

- This is an informational audit signal, not a risk score or proof of compromise.
- Mobile network changes, VPNs, proxies, app versions, browsers, or devices can produce a difference.
- Missing values are not treated as a mismatch.
- The event never blocks login, revokes sessions, or changes permissions.
- Events are deduplicated by the new Nexora session ID.
- IP and User-Agent are untrusted metadata; trusted proxy handling must be configured before using IP for operational analytics.

## Revocation semantics

- Revocation blocks access to Nexora APIs for that session.
- It does not necessarily invalidate the Firebase ID token at Firebase or sign the device out of Firebase itself.
- Other sessions with different Firebase `auth_time` values remain active.
- Firebase Admin refresh-token revocation remains a separate account-wide emergency action.
- The user may need to sign in again to establish a new session after revocation.

## Operational notes

- Session activity writes are throttled to at most approximately once per five minutes per active session.
- Only the latest 50 sessions are returned.
- IP and User-Agent values are untrusted metadata and must not be used for authorization or risk decisions by themselves.
- A Firebase reauthentication event that changes `auth_time` creates a new Nexora session record.
- Session records and revocation timestamps should be included in backups and retention policy.

## Remaining hardening

1. Add rate limits to session listing and revoke operations.
2. Add a confirmation/step-up requirement before revoking sessions in sensitive contexts.
3. Add session expiration and cleanup policy based on product security requirements.
4. Design risk scoring only after trusted proxy, privacy, and false-positive policies are configured.
5. Consider a transactional outbox for reliable audit-event delivery under database failures.
6. Test concurrent revoke-vs-request behavior against the production database engine.

This is server-enforced per-authentication-session revocation, not hardware-backed device identity or remote Firebase sign-out.
