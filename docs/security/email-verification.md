# Email verification flow

## Current behavior

- Firebase Authentication owns delivery and validation of email verification links.
- New email/password registrations request a verification email after the display name is saved.
- A temporary email-delivery failure does not invalidate or sign out the newly created account.
- The account screen shows the current Firebase verification state, allows a resend, and can reload the Firebase user to refresh that state.
- Password reset responses remain intentionally generic to reduce account enumeration.

## Trust boundary

The mobile UI is not an authorization boundary. A client-side `emailVerified` value must never be used to grant a paid plan, privileged role, or access to another product.

The API currently verifies Firebase ID tokens and resolves the provider subject to a canonical Nexora UUID. It does not yet require the Firebase `email_verified` claim for every authenticated endpoint. This is deliberate until public, limited, and sensitive API routes have been classified and a recovery path is in place.

Before production:
1. Define endpoint policy tiers: public, authenticated-basic, verified-email, and step-up/MFA.
2. Enforce the verified-email claim server-side only on routes that require it.
3. Ensure account recovery and verification-resend paths remain reachable for unverified users.
4. Add tests for missing, false, and true `email_verified` claims.
5. Configure Firebase authorized domains, action URL, sender identity, and abuse protections.
6. Add rate limits and security-event records for verification requests and sensitive account changes.

## Session note

Firebase refresh-token revocation is account-wide. It is not a per-device session-revocation mechanism. Device inventory and per-device revocation require a separate server-owned session model before those controls are presented as available.
