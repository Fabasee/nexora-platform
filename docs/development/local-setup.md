# Local Development

## API
1. Create a virtual environment with Python 3.12+.
2. Install `services/api/requirements.txt`.
3. Copy `services/api/.env.example` to `services/api/.env` and adjust local values.
4. From `services/api`, run `python manage.py migrate`, then `python manage.py runserver`.
5. Check `GET /api/v1/health/`.
6. Configure Firebase Admin credentials only in a local secret file outside source control. Set `FIREBASE_PROJECT_ID` and `FIREBASE_CREDENTIALS_PATH` when testing authenticated endpoints.

## Mobile
1. Install Node.js LTS and a package manager.
2. From `apps/mobile`, install dependencies.
3. Copy `.env.example` to `.env` and configure the API origin and Firebase client values.
4. Start Expo with `npx expo start`.
5. Set `EXPO_PUBLIC_API_BASE_URL` to an API URL reachable from the device or emulator.

Do not put server secrets in `EXPO_PUBLIC_*` variables; Expo public variables are bundled into the client. Firebase Admin service-account credentials belong only on the server.
