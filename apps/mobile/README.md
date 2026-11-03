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
