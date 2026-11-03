# Nexora Mobile

React Native application built with Expo Router and TypeScript.

## Local development

```bash
npm install
cp .env.example .env
npx expo start
```

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
3. Register the Android/iOS app identifiers used by development and production builds.
4. Copy the Firebase web app configuration values into the local `.env` file. These client identifiers are public; service-account credentials are not.
5. Add the Firebase project ID and service-account credentials to the API runtime environment separately.
6. Configure authorized email action domains and password reset behavior in Firebase Authentication settings.

The app currently supports email/password registration, sign-in, password reset, and local sign-out. Email verification UX, MFA, device/session inventory, account recovery escalation, App Check enforcement, and production abuse controls are not yet implemented. Do not treat this foundation as a production identity service until those controls and deployment configuration are reviewed.
