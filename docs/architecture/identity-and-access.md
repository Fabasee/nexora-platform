# Identity, account control, and product access

Status: architecture baseline for implementation. This document is normative until superseded by a recorded architecture decision.

## Goals
- Give a person one Nexora identity that can be used across separately operated Nexora products.
- Keep product data, authorization, and lifecycle decisions inside each owning product domain.
- Support Firebase Authentication as an identity provider without making Firebase UID the platform's primary database key.
- Make account linking, provider changes, and future identity providers possible without changing product-owned records.
- Deny access when identity, product membership, entitlement, or resource ownership cannot be established.

## Domain boundaries

### Identity
Owns the canonical Nexora person record and external identity bindings.
- NexoraUser: immutable UUID primary key, lifecycle status, timestamps.
- IdentityProviderAccount: provider name + provider subject, linked to one Nexora user.
- Provider subject is unique within its provider; email and phone are profile/verification attributes, never identity keys.
- A provider account may be linked only through a verified authentication/linking flow.
- Never merge two Nexora users merely because their email or phone strings match.

### Account control
Owns platform-level account security and session state.
- AccountSession: session/device metadata, issued/revoked timestamps, and session status.
- SecurityEvent: append-only security audit events.
- Account control may revoke sessions and suspend a Nexora account.
- It does not own product-specific roles or product content.

### Product registry and access
Owns the registry of Nexora products and the platform-level grant that a user may enter a product.
- Product: stable product key, lifecycle state, metadata.
- ProductMembership: user-to-product relationship and membership state.
- Entitlement: plan/feature grant with explicit scope and validity window.
- A platform product grant is not a substitute for authorization inside the product.

### Product domains
Each product owns its own users' workspaces, content, roles, permissions, and data.
- Product APIs must enforce product and resource scope on every request.
- A token valid for Product A does not imply access to Product B.
- Cross-product data sharing requires an explicit purpose, grant, and auditable operation.
- Never expose a shared database query or Firebase collection as an authorization boundary.

## Authentication contract
1. The mobile client authenticates with the configured provider (initially Firebase Authentication).
2. The client sends the provider ID token over TLS to the Nexora API.
3. A provider adapter verifies signature, issuer, audience/project, expiry, and revocation policy using the provider SDK.
4. The adapter returns a provider-neutral verified identity: provider key, stable subject, authentication time, and verified claims needed by policy.
5. The identity application service resolves the unique provider binding and canonical Nexora UUID.
6. The API applies account status, product membership, entitlement, and resource policy before returning protected data.
7. Internal APIs use the canonical UUID; never trust a client-supplied user ID or role.

Do not store provider passwords or private service-account credentials in the platform database or repository. Firebase Admin initialization must remain lazy and isolated behind the infrastructure adapter.

## Account linking and recovery
- Linking a second provider requires a recently authenticated session and proof of control of the new provider.
- Conflicts are explicit: if the provider subject is already linked to another Nexora UUID, reject and create a security event; do not silently merge.
- Unlinking must preserve at least one viable sign-in method or a documented recovery path.
- Recovery and high-risk changes require step-up verification.
- Account suspension blocks new sessions and protected product access; product data retention/deletion follows each product's policy and applicable law.

## Minimum persistence constraints
- NexoraUser.id: UUID, immutable.
- IdentityProviderAccount: UUID primary key; user_id FK; provider + provider_subject unique constraint; timestamps.
- Product.key: unique stable slug.
- ProductMembership: unique (user_id, product_id).
- Entitlement: explicit subject, product, feature, scope, status, starts_at, ends_at; no implicit Pro boolean.
- Use database transactions for first-login creation and account linking. Handle uniqueness races by reloading the winning binding and verifying it belongs to the same canonical user.

## Not in the first implementation
- Automatic identity merge by email/phone.
- Global product roles that bypass product authorization.
- A universal data lake with unrestricted product access.
- Password storage in Nexora when authentication is delegated to Firebase.
- AI training access to customer data by default.

## Implementation sequence
1. Lock the custom user model and UUID strategy before the first production migration.
2. Implement identity entities, constraints, repositories, and provider-neutral service contracts.
3. Add Firebase token verification adapter and deterministic fake-provider tests.
4. Implement session/account control and security event audit.
5. Implement product registry, memberships, entitlements, and policy checks.
6. Add per-product authorization integration tests and concurrency tests.
7. Only then expose sign-in and product-launch flows in the mobile app.
