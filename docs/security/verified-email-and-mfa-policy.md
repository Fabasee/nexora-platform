# Verified email and sensitive API access

## Trust boundary

Email verification is determined only from the `email_verified` claim in an ID token that has passed Firebase Admin verification with revocation checking enabled. The mobile UI's local `user.emailVerified` value is informational and is never accepted as authorization evidence.

The authentication layer copies this verified claim into the Nexora request context and synchronizes it to the server-side identity session. When the claim changes from false to true, the API records an `identity.email_verification_confirmed` security event.

## Enforcement

The initial policy requires verified email for the product catalog endpoint:

`GET /api/v1/products/`

The central account, security-event, and session-management endpoints remain available to authenticated but unverified accounts so that users can complete verification and manage account security.

The API returns the verified state from the authenticated request context on:

`GET /api/v1/account/me/`

The mobile app reloads the Firebase user, forces an ID-token refresh, and reads the account endpoint again when the user checks verification status. This ensures the backend sees the updated claim rather than relying on stale client state.

## Rate limiting

Session revocation uses a scoped authenticated-user throttle of 10 requests per hour. Global API throttles remain in place. These DRF throttles are application-level controls and should be complemented by edge/WAF rate limits and monitoring in production.

## MFA status

MFA enrollment and second-factor challenge flows are not yet implemented in the Expo client. Do not treat email verification as MFA. Do not claim an account is MFA-protected until the Firebase Authentication multi-factor enrollment and sign-in challenge are implemented and tested in a native development build.

The next implementation stage should:
1. Confirm Expo SDK and Firebase JS SDK support for the chosen native MFA flow.
2. Select a supported factor (for example, phone SMS or TOTP) and its abuse controls.
3. Implement enrollment, verification challenge, recovery, and factor removal with step-up authentication.
4. Enforce MFA for high-risk account changes and sensitive product operations.
5. Test account recovery and lost-device scenarios before production rollout.

## Limitations

- Product catalog is the first protected resource; individual product APIs must explicitly adopt the same permission or a stronger policy.
- A verified email does not establish legal identity or guarantee account ownership indefinitely.
- Rate limits depend on a correctly configured shared cache in multi-instance production.
- IP and User-Agent are untrusted signals and are not sufficient by themselves to block a login.
