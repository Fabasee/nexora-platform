# Public Repository Checklist

Before every push or release:

- [ ] No populated `.env`, API keys, access tokens, signing keys, or Firebase service-account JSON.
- [ ] No production database, exports, logs, screenshots containing personal data, or test credentials.
- [ ] Firebase rules deny access unless a collection/path has an explicit least-privilege policy.
- [ ] Client-side configuration contains no privileged secrets.
- [ ] Dependency changes are intentional and lockfiles are updated.
- [ ] CI and security checks pass; failures are not hidden or bypassed.
