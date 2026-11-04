# ADR 0002: Native Firebase Authentication for mobile MFA

- Status: Accepted for implementation planning; migration not yet applied
- Date: 2026-11-04
- Decision owners: Nexora platform

## Context

The mobile app currently initializes Firebase Authentication through the Firebase JavaScript SDK with React Native AsyncStorage persistence. Nexora's API already verifies Firebase ID tokens using Firebase Admin and records server-verified MFA claims.

Firebase Identity Platform supports TOTP MFA on Android and iOS native SDKs. Expo's Firebase guide distinguishes the Firebase JS SDK from React Native Firebase: React Native Firebase wraps native SDKs and requires custom native code plus an Expo development build. Expo Go cannot load these native modules.

The React Native Firebase Auth module exposes multi-factor APIs, including TOTP factor types. Its MFA guide documents TOTP and phone MFA flows. Therefore, using the JS SDK as the only mobile auth provider would be an unsupported assumption for the production native TOTP flow.

## Decision

1. Keep Firebase Authentication with Identity Platform as the identity provider and Nexora's internal UUID as the canonical account anchor.
2. For Android and iOS, adopt React Native Firebase Auth as the native authentication adapter after a compatibility proof-of-concept against the selected Expo SDK / React Native versions.
3. Add Expo Development Client and native config plugins only as part of that migration; do not claim Expo Go support for native MFA.
4. Keep the current Firebase JS SDK implementation unchanged until the native adapter passes the same auth contract tests and a device-level MFA enrollment/sign-in test.
5. If the app ships web, retain a platform-specific web adapter using the Firebase JS SDK. Do not mix JS SDK and native SDK user instances within one platform runtime.
6. Preserve the existing backend token contract: Firebase ID token in Bearer authorization, verified with Firebase Admin and revocation checking. The backend remains provider-neutral and does not store TOTP secrets.
7. Do not require MFA globally until a second factor and a tested recovery path are available.

## Migration acceptance criteria

- [ ] Confirm compatible React Native Firebase app/auth package versions for the repository's Expo SDK and React Native versions.
- [ ] Add an Expo development build and Android/iOS Firebase native configuration without committing private service credentials.
- [ ] Implement platform-specific Firebase Auth adapter with a stable interface for sign-in, registration, password reset, email verification, sign-out, token retrieval, and MFA.
- [ ] Preserve AsyncStorage-backed auth persistence and ensure no duplicate Firebase app/auth instances.
- [ ] Implement TOTP enrollment: recent reauthentication, generate secret, show QR and manual secret, verify initial code, then enroll.
- [ ] Implement TOTP challenge after `auth/multi-factor-auth-required` and resolve sign-in before app navigation.
- [ ] Support at least one additional factor or a secure recovery workflow before mandatory MFA.
- [ ] Confirm Firebase ID token includes a recognized `firebase.sign_in_second_factor` claim after completed MFA.
- [ ] Run backend tests, mobile typecheck, Expo prebuild, Android/iOS development build, and real-device end-to-end tests.
- [ ] Verify factor removal requires recent reauthentication and emits a security audit event.

## Consequences

- Expo Go is no longer a sufficient test environment for native MFA.
- The mobile authentication adapter needs a deliberate migration and regression suite.
- Native Firebase configuration files must be supplied through secure project configuration and must not be committed if they contain sensitive environment-specific data.
- No custom MFA secret storage is added to Nexora's database.
