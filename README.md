# Nexora Platform

A modular, service-ready foundation for the Nexora multi-product ecosystem.

> Public repository: never commit credentials, private keys, production environment files, service-account JSON, or user data.

## Stack

- Mobile: React Native, Expo SDK 57, Expo Router, TypeScript
- API: Django 5.2 and Django REST Framework
- Identity provider: Firebase Authentication
- Server integration: Firebase Admin SDK behind a lazy infrastructure adapter
- Architecture: Modular Monolith → Service-Ready

## Core principles

1. One Nexora identity does not imply shared access to every product's data.
2. Product domains own their data and authorization policies.
3. The canonical Nexora UUID is independent of Firebase UID and future identity providers.
4. Provider tokens are verified by the API; client-supplied user IDs and roles are never trusted.
5. Product membership and feature entitlements are separate authorization decisions.
6. Default-deny authorization, explicit scopes, and secret-free source control.
7. Keep infrastructure replaceable and test boundaries explicitly.

## Repository layout

```text
apps/mobile/             Expo Router application and Firebase client
services/api/            Django REST API
  apps/core/             Health and shared API primitives
  apps/identity/         Canonical Nexora UUID and provider bindings
  apps/products/         Product registry, memberships, entitlements
  apps/integrations/     Firebase Admin infrastructure adapter
infra/firebase/          Deny-by-default security rules
docs/architecture/       System design and architecture decisions
docs/security/           Security standards and public-repository checklist
docs/development/        Local setup and contribution workflow
```

## Implemented foundation

- Expo mobile shell with a responsive Nexora ecosystem home screen.
- Firebase client initialization and authentication-state provider.
- Email/password sign-in, registration, password reset, and account overview screens.
- Typed API client for the authenticated product catalog.
- Django API with a custom UUID-based Nexora user model.
- Firebase ID-token verification with revocation checks.
- Provider-neutral identity resolution with a unique provider-subject constraint.
- Product registry, product membership, time-bounded feature entitlements, product plans, and subscriptions.
- Governed master portfolio registry separating confirmed applications, modules, platform services and unvalidated candidate ideas.
- Version-controlled portfolio seed at `docs/product-registry/master-product-registry.json`, synchronized non-destructively with `python manage.py sync_product_registry`.
- First-use product activation that idempotently provisions a product's Free plan without enrolling users in every product.
- Authenticated subscription status API scoped to the current Nexora identity.
- Scoped entitlement checks that fail closed when scope does not match.
- Authenticated current-account endpoint at `GET /api/v1/account/me/`.
- Account-scoped security-event history at `GET /api/v1/account/security-events/`.
- Server-managed identity sessions with per-session revocation.
- Server-verified email status and verified-email enforcement for the product catalog.
- Scoped rate limit for session revocation operations.
- Authenticated product catalog endpoint at `GET /api/v1/products/`.
- Account-scoped live product catalog at `GET /api/v1/products/catalog/`, including each product's activation and subscription state.
- Expo product catalog screen with server-backed Free activation at `apps/mobile/app/catalog.tsx`.
- Product activation endpoint at `POST /api/v1/products/{product_key}/activate/` and current subscription endpoint at `GET /api/v1/products/{product_key}/subscription/`.
- Django migrations, focused identity/access tests, and GitHub Actions checks.

## Local checks

API:

```bash
cd services/api
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test
```

Mobile:

```bash
cd apps/mobile
npm install
npm run typecheck
npx expo install --check
```

## Security notes

Firebase client configuration is public application metadata, not an authorization mechanism. The API verifies ID tokens using Firebase Admin. Firebase Admin service-account credentials and Django secrets must remain outside source control.

The current mobile authentication layer supports Firebase email/password registration, sign-in, password reset, email verification, local sign-out, account overview, security-event history, and device-session revocation. The API enforces verified email for the product catalog. MFA enrollment and challenge flows, production abuse controls, shared-cache rate limiting, retention policy, and production deployment review are still pending. Product-specific data APIs and product roles must be implemented in their owning domains.

## Project status

Foundation implementation in progress on `feat/platform-foundation`. The `main` branch is intentionally unchanged until the foundation is reviewed.
