# Nexora Mobile

React Native application built with Expo Router and TypeScript.

## Local development

```bash
npm install
cp .env.example .env
npx expo start --dev-client
```

For the first native build, install the Expo development client and React Native Firebase modules already declared in `package.json`. Expo Go is not supported for native Firebase Auth.

Configure the following public client values in `.env`:

- `EXPO_PUBLIC_API_BASE_URL`: Nexora Django API origin, without the `/api/v1` suffix.
- `EXPO_PUBLIC_FIREBASE_API_KEY`
- `EXPO_PUBLIC_FIREBASE_AUTH_DOMAIN`
- `EXPO_PUBLIC_FIREBASE_PROJECT_ID`
- `EXPO_PUBLIC_FIREBASE_APP_ID`

Use your computer's LAN IP for a physical device. Android emulators commonly reach the host machine through `10.0.2.2`; `localhost` inside an emulator refers to the emulator itself.

Expo public variables are bundled into the client. Firebase client configuration values are identifiers, not service-account secrets. Never place Firebase Admin credentials, private keys, or Django secrets in this app.

## Firebase Authentication setup

1. In Firebase Console, open **Authentication → Sign-in method**.
2. Enable **Email/Password**. Do not enable anonymous sign-in for this account flow.
3. Register an Android app with package ID `com.nexora.platform.mobile` and an iOS app with bundle ID `com.nexora.platform.mobile` in Firebase Project Settings. These IDs must match the Expo app config.
4. Download the Android `google-services.json` and iOS `GoogleService-Info.plist` client configuration files. Place them in `apps/mobile/`. They are intentionally git-ignored and must never be replaced with Firebase Admin service-account credentials.
5. Keep the existing web app configuration values in `.env` for the web Firebase JS SDK adapter. The native adapter reads the registered platform app configuration through the native Firebase SDK.
6. Add the Firebase project ID and service-account credentials to the API runtime environment separately.
7. Configure authorized email action domains and password reset behavior in Firebase Authentication settings.

The mobile authentication UI currently supports email/password registration, sign-in, password reset, email verification retry, account/session inventory, and local sign-out. Authentication operations are routed through the provider-neutral contract in `src/lib/auth-types.ts`; `src/lib/firebase-js-auth.ts` is the current Firebase JS SDK adapter. This separation is the migration seam for the planned React Native Firebase native adapter and keeps the Nexora API bearer-token contract unchanged. The Android/iOS adapter now uses React Native Firebase Auth 27.1.0, while web retains the Firebase JS SDK adapter. The Expo config applies React Native Firebase plugins and dynamic iOS frameworks; native Firebase configuration files are loaded only when present. Run `npx expo prebuild --clean` after adding the native config files, then `npx expo run:android` or create an EAS development build with `eas build --profile development --platform android`. iOS builds require macOS/Xcode locally or EAS Build. MFA enrollment/challenge/recovery UI, App Check enforcement, and production abuse controls are still pending. Do not treat MFA as active until the native TOTP flows, recovery paths, Firebase Identity Platform configuration, and device end-to-end tests are complete.
