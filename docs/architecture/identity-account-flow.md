# Identity and Account Flow

## Purpose

Nexora uses a provider-neutral internal UUID as its canonical account identifier. Firebase Authentication is the current credential provider, not the owner of product authorization.

## Sign-in lifecycle

1. The mobile app signs in or registers with Firebase Authentication using email and password.
2. Firebase returns an ID token to the mobile client.
3. The client sends that token as `Authorization: Bearer <id-token>` to the API.
4. The API verifies the token with Firebase Admin, including revocation checking.
5. The API maps the verified Firebase UID to `IdentityProviderAccount`.
6. If this is a first login, the API creates a Nexora UUID and a unique provider binding in one database transaction.
7. Suspended or deactivated Nexora identities are rejected.
8. Product APIs independently enforce product membership and feature entitlements.

## Account API

- `GET /api/v1/account/me/`: returns the authenticated internal UUID, account status, creation time, and provider names/last-authenticated timestamps.
- Provider subjects, ID tokens, credentials, and service-account data are never returned.
- The endpoint requires Firebase token authentication; it is not a public profile lookup.

## Security invariants

- Never accept a Nexora user ID, role, product key, or entitlement from an untrusted client as proof of access.
- Never auto-link two provider accounts merely because their email strings match.
- Provider linking requires a future explicit, recent-authentication, verified-account workflow.
- Product data remains isolated by product domain and server-side authorization.
- Firebase Admin credentials and Django secrets exist only in server runtime secret storage.
- The client may display account status, but the API is authoritative for authorization.

## Current implementation boundaries

Implemented: Firebase email/password sign-in, registration, password reset, local sign-out, ID-token verification, internal identity mapping, account overview, and product access checks.

Not yet implemented: email verification enforcement, MFA, explicit provider linking/unlinking, device/session inventory and revocation UI, security-event audit trail, account deletion workflow, App Check enforcement, risk-based authentication, and production rate-limit/abuse review.

Do not expose product data or mark the identity foundation production-ready until the missing controls are designed, implemented, and tested.
