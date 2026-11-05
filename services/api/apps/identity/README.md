# Identity application

This app owns the canonical Nexora UUID identity and provider-account bindings.

- Firebase is an authentication provider, not the canonical user database key.
- Provider tokens are verified by the infrastructure SDK adapter before identity resolution.
- Product roles and product data do not belong in this app.
- New API views are protected by default through DRF's Firebase bearer authenticator and IsAuthenticated permission.
- Public endpoints must opt out explicitly and narrowly, as the health endpoint does.

Do not add password login or automatic email-based account merging here.
