# Security Baseline

- Public repository: never commit secrets, access tokens, private keys, service-account files, database dumps, or real user data.
- Production configuration must fail closed when required secrets or security settings are absent.
- Use HTTPS in deployed environments; configure trusted hosts, CORS, CSRF, secure cookies, and proxy headers explicitly.
- Authentication establishes identity; authorization is checked for every resource and product boundary.
- Apply least privilege to Firebase IAM and deny-by-default Firestore/Storage rules.
- Validate JWT/token issuer, audience, signature, expiry, and revocation policy through trusted provider adapters.
- Rate-limit sensitive endpoints and log security events without logging credentials or raw tokens.
- Rotate credentials after suspected exposure and review repository history, not just the current tree.
- Threat-model account linking, session revocation, account recovery, and cross-product access before shipping identity features.
