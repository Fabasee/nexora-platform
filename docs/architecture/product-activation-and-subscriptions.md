# Product activation and subscription lifecycle

## Default access policy

A Nexora identity does not automatically receive memberships in every product. A product is activated on the user's first explicit launch. The API then creates an active membership and the product's zero-price Free plan in one database transaction.

This provides a low-friction first-use experience without silently enrolling every account in every product. A product that has not been opened has no membership or subscription record.

## Data ownership

- Product: platform product registry and lifecycle.
- ProductPlan: a product-owned Free or Pro offer, price and billing interval.
- PlanFeature: the feature grants included in a plan.
- ProductMembership: whether the account may enter the product.
- ProductSubscription: the account's current plan for that product.
- Entitlement: the time-bounded feature grant checked by product APIs.

A platform membership or subscription is not a substitute for product-domain authorization. Each product API must still enforce its own roles, resource ownership and scopes.

## Activation API

POST /api/v1/products/{product_key}/activate/

- Requires a Firebase-verified Nexora identity and verified email.
- Creates the product's Free plan if it has not been configured yet.
- Creates an active membership and Free subscription on first activation.
- Is idempotent for repeated launches.
- Never downgrades an existing active Pro subscription.
- Rejects suspended or revoked memberships.
- Rejects inactive, maintenance or retired products.
- Returns the current plan and whether membership/subscription records were created.

GET /api/v1/products/{product_key}/subscription/

Returns only the authenticated user's subscription for the requested product. Returns 404 product_not_activated if no subscription exists.

GET /api/v1/products/

Continues to return products with active memberships only.

## Free and Pro boundaries

The activation endpoint only grants Free. It does not accept a client-supplied plan, price, amount, entitlement, or payment status. Pro activation must be implemented through a trusted server-side payment verification workflow before changing ProductSubscription.plan.

Plan features are configured by platform administrators. Activation copies the Free plan's feature definitions into user/product entitlements. No default feature is granted merely because the Free plan exists.

Amounts are stored as integer minor units with an ISO currency code. Payment provider integration, tax handling, refunds, proration, renewal, cancellation UX, and subscription event reconciliation are deliberately outside this phase.

## Operational requirements before production

- Configure each product's Free and Pro feature matrix.
- Add payment-provider webhook verification before offering paid upgrades.
- Add subscription history and immutable billing events before processing real payments.
- Add concurrency tests against the production database engine.
- Confirm verified-email policy and account recovery requirements.
- Monitor activation abuse and apply rate limits appropriate to product launches.
