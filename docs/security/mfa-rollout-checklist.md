# MFA rollout and device validation checklist

This checklist is an operator-run prerequisite. Do not enable mandatory MFA until every required test is complete.

## Client implementation status

- [x] Native Android/iOS authentication adapter using React Native Firebase Auth 27.1.0.
- [x] Reauthentication with current password before TOTP enrollment and factor removal.
- [x] TOTP enrollment secret generation and six-digit enrollment verification.
- [x] TOTP sign-in challenge resolution before authenticated navigation.
- [x] Factor inventory and factor removal UI.
- [x] Clear the in-memory enrollment secret on completion, cancellation, and sign-out.
- [x] Local QR code rendering using `react-native-qrcode-svg` + `react-native-svg`; manual secret remains available as fallback.
- [ ] Recovery codes, alternate-factor recovery, and account recovery workflow.
- [ ] Android/iOS development builds and end-to-end device validation.

The completed items above describe code implementation only; they do not mean the Firebase project is configured or that MFA is live for users.

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
- [ ] Verify QR code and manual secret are displayed only in the enrollment flow; confirm neither the TOTP secret nor `otpauth` URI is logged, persisted, or sent to any remote service.
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
