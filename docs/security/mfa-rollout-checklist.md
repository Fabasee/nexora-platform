# MFA rollout and device validation checklist

This checklist is an operator-run prerequisite. Do not enable mandatory MFA until every required test is complete.

## Firebase project prerequisites

- [ ] Confirm the Firebase project is upgraded to Firebase Authentication with Identity Platform.
- [ ] Enable TOTP as a supported second factor in the Identity Platform configuration.
- [ ] Confirm at least one first-factor provider supports MFA.
- [ ] Enforce verified email before factor enrollment.
- [ ] Set appropriate allowed factors and recovery policy.
- [ ] Configure SMS regions only if SMS is deliberately enabled; do not enable SMS as an unreviewed fallback.
- [ ] Register Android and iOS app identifiers and configure native Firebase app files through secure project setup.

## Mobile build prerequisites

- [ ] Confirm React Native Firebase app/auth versions are compatible with the repository's Expo SDK and React Native versions.
- [ ] Install and configure Expo Development Client and native config plugins.
- [ ] Build and install a development client for each target platform.
- [ ] Verify sign-in, registration, password reset, email verification, token refresh, and sign-out before enabling MFA.

## TOTP enrollment tests

- [ ] Reject enrollment when email is not verified.
- [ ] Require recent reauthentication before generating an enrollment secret.
- [ ] Display QR code and manual secret only in the enrollment flow.
- [ ] Never log, persist, or send the TOTP secret to Nexora API.
- [ ] Reject invalid or expired TOTP codes.
- [ ] Confirm successful enrollment updates Firebase factor metadata and ID token claims.
- [ ] Confirm the backend marks the Nexora session as MFA-verified only after Firebase Admin verifies the token.

## Sign-in and recovery tests

- [ ] Confirm password-only sign-in for a TOTP-enrolled user is held at the Firebase MFA challenge.
- [ ] Confirm the app does not navigate to authenticated routes before resolver completion.
- [ ] Confirm a valid TOTP resolves sign-in and the API recognizes the MFA claim.
- [ ] Confirm invalid, expired, replayed, and cancelled challenges fail closed.
- [ ] Test lost authenticator recovery and second-factor removal with recent reauthentication.
- [ ] Test account recovery support without bypassing the Firebase MFA requirement silently.

## API and operational tests

- [ ] Confirm client-supplied `mfa_verified` or factor names never grant access.
- [ ] Confirm the `VerifiedMFARequired` permission denies requests without server-verified MFA context.
- [ ] Apply the permission only to endpoints whose product policy requires MFA.
- [ ] Configure shared cache and edge rate limits before production.
- [ ] Monitor MFA enrollment, challenge failures, recovery, factor removal, and suspicious session churn.
- [ ] Keep MFA optional until recovery and production abuse controls are validated.
