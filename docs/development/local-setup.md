# Local Development

## API
1. Create a virtual environment with Python 3.12+.
2. Install `services/api/requirements.txt`.
3. Copy `services/api/.env.example` to `services/api/.env` and adjust local values.
4. From `services/api`, run `python manage.py migrate`, then `python manage.py runserver`.
5. Check `GET /api/v1/health/`.

## Mobile
1. Install Node.js LTS and a package manager.
2. From `apps/mobile`, install dependencies.
3. Start Expo with `npx expo start`.
4. Set `EXPO_PUBLIC_API_URL` to the reachable API URL for your device/emulator.

Do not put server secrets in `EXPO_PUBLIC_*` variables; Expo public variables are bundled into the client.
