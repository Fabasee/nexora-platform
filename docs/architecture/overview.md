# Platform Architecture

## Direction
Nexora Platform is a modular monolith designed to become service-ready without coupling domain logic to today's infrastructure choices.

## Logical layers
1. **Presentation** — Expo Router mobile client.
2. **API interface** — Django REST Framework serializers, views, authentication, throttling, and versioned URLs.
3. **Application** — use cases and orchestration.
4. **Domain** — identity, product access, policy, and business invariants; no framework/vendor imports.
5. **Infrastructure** — Django persistence, Firebase adapters, messaging, storage, and external providers.

Dependencies point inward. Infrastructure implements contracts owned by application/domain layers.

## Identity and product isolation
- Nexora identity is the stable account anchor.
- Product membership, sessions, roles, entitlements, and resource permissions are distinct concepts.
- Every request must resolve an authenticated principal and then authorize access to the target product/resource.
- Never trust a client-supplied product ID, role, owner ID, or entitlement without server-side verification.
- Cross-product access requires an explicit, auditable policy; it is never implied by a shared login.

## Firebase boundary
Firebase is an optional infrastructure provider, not the platform's source of domain truth by default. Admin SDK usage belongs in backend adapters. Client Firebase SDKs must not bypass backend authorization for protected platform data. Keep provider-neutral contracts so Firebase can be replaced.

## Initial implementation boundary
The first slice provides a mobile shell and a minimal Django health endpoint. Identity, sessions, RBAC, entitlements, and product data will be introduced as separate reviewed domains with migrations and tests.
