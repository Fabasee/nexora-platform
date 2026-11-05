# Nexora Office Web

Private internal operations console for the Nexora ecosystem. This application is intentionally separate from the consumer mobile application.

## Requirements

- Node.js 22+
- Firebase Web app configuration for the existing Nexora Firebase project
- Nexora Django API reachable at `/api/v1` on the same origin (recommended)

## Local development

1. Copy `.env.example` to `.env`.
2. Set the Firebase Web app values. These are public client configuration values; never place Firebase Admin credentials, service-account JSON, or Django secrets here.
3. Keep `VITE_API_BASE_URL=/api/v1` for same-origin development, or set an explicit API origin if your infrastructure has an approved CORS policy.
4. Start the Django API on `http://127.0.0.1:8000`.
5. Run:

```bash
npm install
npm run typecheck
npm run dev
```

The Vite development server proxies `/api` to the local Django API. Open `http://localhost:4173`.

## Access model

- Sign-in only; there is no public registration flow in Office.
- Firebase Authentication provides the identity token.
- The API verifies the token and enforces both verified-email and staff permissions on every Office request.
- Hiding the dashboard in the browser is not an authorization boundary. A non-staff account must receive HTTP 403 from the API.
- The browser never sends a role, user ID, or staff flag as proof of authorization.
- API calls obtain a fresh Firebase ID token through the Firebase SDK.
- Portfolio endpoints are read-only in this phase. Registry changes remain in the reviewed Django Admin/manifest workflow.

## Production deployment

Serve the built `dist/` directory behind the same trusted origin as the API, routing `/api/v1/*` to Django and all Office app routes to the static application. This avoids introducing permissive cross-origin access. Enforce HTTPS, trusted host configuration, Firebase authorized domains, and appropriate CSP/security headers at the edge.

## Current scope

- Staff sign-in and verified-email UX
- Portfolio summary metrics
- Search and filters for type, lifecycle, and decision status
- Application/module grouping and detail drawer
- Read-only mode; no write or publish controls
- Responsive desktop and mobile layout
