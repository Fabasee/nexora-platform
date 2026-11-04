# Verified email, MFA, and sensitive API access

## Trust boundary

Email verification is determined only from the `email_verified` claim in an ID token that has passed Firebase Admin verification with revocation checking enabled. The mobile UI's local `user.emailVerified` value is informational and is never accepted as authorization evidence.

MFA is determined only from the reserved Firebase ID-token claim `firebase.sign_in_second_factor`, after the token has passed Firebase Admin verification. Nexora currently accepts the documented factor identifiers `phone` and `totp`. Client-supplied flags, request bodies, local storage, and Firebase user profile fields are never accepted as proof of MFA.

The API copies these trusted claims into the resolved Nexora request context and its server-side session record. It records `identity.mfa_authenticated` once per session when a second-factor-authenticated session is first observed.

## Enforcement

The initial policy requires verified email for the product catalog endpoint:

`GET /api/v1/products/`

The central account, security-event, and session-management endpoints remain available to authenticated but unverified accounts so users can complete verification and manage account security.

The API returns `email_verified`, `mfa_verified`, and `second_factor_type` for the current authenticated session from `GET /api/v1/account/me/`. The session inventory also reports whether each session was authenticated with a recognized second factor.

`VerifiedMFARequired` is available for sensitive API views. It must be added explicitly to each endpoint that requires MFA; it is not globally enabled and does not silently change the product catalog policy.

## MFA provider decision

Use Firebase Authentication with Google Cloud Identity Platform's TOTP MFA capability as the preferred authenticator-app factor. TOTP avoids SMS delivery costs and SIM-swap exposure. Keep a second enrolled factor or a documented account recovery process before making MFA mandatory.

Firebase's documented TOTP MFA flow uses the modular Firebase JavaScript SDK and requires upgrading the Firebase project to Identity Platform with TOTP enabled. The current Expo app uses the Firebase JS SDK. For Android and iOS, the selected implementation path is a deliberate migration to React Native Firebase Auth plus Expo Development Client, after confirming package compatibility with the repository's Expo SDK and React Native versions. React Native Firebase exposes native MFA APIs, including TOTP. Expo Go cannot load its native modules. See ADR 0002 and the MFA rollout checklist. The existing JS SDK auth adapter remains in place until the native adapter passes end-to-end regression tests. Expo Go alone is not sufficient evidence for validating native production behavior.

The app must implement:
1. Reauthenticate the current user before enrollment, factor removal, or other sensitive MFA changes.
2. Generate a Firebase TOTP enrollment secret from a valid MFA session and show the QR code/secret only during enrollment.
3. Require a valid authenticator code to complete enrollment.
4. Catch `auth/multi-factor-auth-required` during sign-in, present the available enrolled factor, and complete the resolver challenge before navigating into the signed-in app.
5. Force-refresh the ID token after enrollment/sign-in and let the API verify the reserved second-factor claim.
6. Enroll and test a second recovery factor or implement a secure support recovery workflow before requiring MFA for all accounts.
7. Provide a clear factor-removal flow with recent reauthentication and audit events.

Do not implement custom TOTP secret storage in the Nexora database. Firebase Identity Platform owns the factor secrets and challenge validation.

## Rate limiting and abuse controls

Session revocation uses a scoped authenticated-user throttle of 10 requests per hour. MFA enrollment, factor removal, and recovery must also have abuse controls, provider quotas, and monitoring. DRF throttles are application-level controls and should be complemented by edge/WAF rate limits and a shared production cache.

## Current limitations

- The backend now recognizes verified Firebase MFA claims, stores MFA state per Nexora session, records MFA authentication events, and exposes an MFA-required permission.
- The mobile native Firebase Auth adapter migration, TOTP enrollment UI, and sign-in challenge UI are not implemented yet.
- The Firebase project has not been confirmed as upgraded to Identity Platform or configured for TOTP.
- No recovery codes are generated or stored by Nexora. Do not claim recovery codes are available; recovery-factor and account recovery design remains pending.
- No API endpoint currently applies `VerifiedMFARequired`; sensitive endpoints must opt in deliberately after client enrollment and challenge are tested.
- MFA is not active for users until the Firebase project configuration and client flows are completed and tested.
- Product catalog is the first protected resource for verified email; individual product APIs must explicitly adopt the same permission or a stronger policy.
- A verified email does not establish legal identity or guarantee account ownership indefinitely.
- Rate limits depend on a correctly configured shared cache in multi-instance production.
- IP and User-Agent are untrusted signals and are not sufficient by themselves to block a login.
