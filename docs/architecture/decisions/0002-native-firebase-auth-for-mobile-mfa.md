# ADR 0002: Native Firebase Authentication for mobile MFA

- Status: Implementation in progress
- Date: 2026-11-04
- Decision owners: Nexora platform

## Context

The mobile app currently initializes Firebase Authentication through the Firebase JavaScript SDK with React Native AsyncStorage persistence. Nexora's API already verifies Firebase ID tokens using Firebase Admin and records server-verified MFA claims.

Firebase Identity Platform supports TOTP MFA on Android and iOS native SDKs. Expo's Firebase guide distinguishes the Firebase JS SDK from React Native Firebase: React Native Firebase wraps native SDKs and requires custom native code plus an Expo development build. Expo Go cannot load these native modules.

The React Native Firebase Auth module exposes multi-factor APIs, including TOTP factor types. Its MFA guide documents TOTP and phone MFA flows. Therefore, using the JS SDK as the only mobile auth provider would be an unsupported assumption for the production native TOTP flow.

## Decision

1. Keep Firebase Authentication with Identity Platform as the identity provider and Nexora's internal UUID as the canonical account anchor.
2. For Android and iOS, adopt React Native Firebase Auth 27.1.0 as the native authentication adapter. Its published peer ranges include Expo >=47 and React Native >=0.60; Expo SDK 57 / React Native 0.86.3 are within those declared ranges.
3. Use Expo Development Client 57.0.20 and Expo Build Properties 57.0.22 for the SDK 57 project. Configure React Native Firebase app/auth plugins and dynamic iOS frameworks; do not claim Expo Go support for native MFA.
4. Keep the Firebase JS SDK adapter for web and select the React Native Firebase adapter for Android/iOS. The native adapter now implements the shared auth contract and TOTP operations; device-level regression remains required.
5. If the app ships web, retain a platform-specific web adapter using the Firebase JS SDK. Do not mix JS SDK and native SDK user instances within one platform runtime.
6. Preserve the existing backend token contract: Firebase ID token in Bearer authorization, verified with Firebase Admin and revocation checking. The backend remains provider-neutral and does not store TOTP secrets.
7. Do not require MFA globally until a second factor and a tested recovery path are available.

## Migration acceptance criteria

- [x] Confirm React Native Firebase app/auth 27.1.0 peer compatibility with Expo SDK 57 / React Native 0.86.3.
- [x] Add Expo Development Client, EAS development profile, config plugins, and ignored native Firebase client config paths. Native app files still need to be supplied locally/EAS.
- [x] Implement platform-selected native and web Auth adapters for sign-in, registration, password reset, email verification, sign-out, and ID-token retrieval. TOTP operations remain pending.
- [x] Preserve the web adapter's AsyncStorage persistence and use the native SDK's platform persistence on Android/iOS. Native default-app configuration is required.
- [x] Implement TOTP enrollment with current-password reauthentication, in-memory secret generation, manual secret display, six-digit verification, and factor enrollment.
- [ ] Add QR rendering to the enrollment flow; manual secret entry is currently supported.
- [x] Implement TOTP challenge after `auth/multi-factor-auth-required` and resolve sign-in before app navigation.
- [ ] Support at least one additional factor or a secure recovery workflow before mandatory MFA.
- [ ] Confirm Firebase ID token includes a recognized `firebase.sign_in_second_factor` claim after completed MFA.
- [ ] Run Expo prebuild, Android/iOS development builds, and real-device end-to-end tests after the Firebase native config files are supplied.
- [x] Require current-password reauthentication before factor removal.
- [ ] Emit and verify a security audit event for factor removal.

## Consequences

- Expo Go is no longer a sufficient test environment for native MFA.
- The mobile authentication adapter needs a deliberate migration and regression suite.
- Native Firebase configuration files must be supplied through secure project configuration and must not be committed if they contain sensitive environment-specific data.
- No custom MFA secret storage is added to Nexora's database.


## Implementation progress (2026-11-04)

- Added `@react-native-firebase/app` and `@react-native-firebase/auth` pinned to 27.1.0.
- Added SDK 57-compatible `expo-dev-client` 57.0.20 and `expo-build-properties` 57.0.22.
- Added platform adapter selection: Android/iOS use React Native Firebase; web retains the existing Firebase JS SDK adapter. A platform runtime uses only one Auth implementation.
- Added dynamic iOS framework configuration required by the current React Native Firebase / Firebase Apple SDK toolchain.
- Added EAS development, preview, and production profiles. Native Firebase client files are git-ignored but included in the mobile EAS archive; Admin service-account credentials remain excluded.
- CI typecheck and Expo dependency compatibility pass on the implementation commit. Native prebuild/device tests are blocked until the project-specific `google-services.json` and `GoogleService-Info.plist` are supplied.
- Implemented native TOTP enrollment and challenge resolution, plus factor inventory/removal with current-password reauthentication. QR rendering and recovery are pending.
- Firebase Identity Platform project configuration, recognized token-claim verification on real devices, and Android/iOS end-to-end tests remain pending. MFA is not active for users.
