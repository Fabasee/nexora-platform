# Nexora Platform — Engineering Agent Guide

## Mission
Build a secure, maintainable platform foundation for multiple independent Nexora products.

## Architecture
- Follow Modular Monolith → Service-Ready. Do not split services prematurely.
- Keep domain/application code independent of Django, Firebase, network clients, and vendor SDKs.
- Put external integrations behind explicit ports and infrastructure adapters.
- A shared identity is not shared authorization: every product resource must be scoped and authorized explicitly.
- Keep product data isolated by domain and enforce tenant/product boundaries server-side.

## Engineering rules
- TypeScript strict mode; avoid `any`, unsafe casts, and unvalidated external data.
- Python type hints for public interfaces; validate at API boundaries.
- Never commit secrets, credentials, personal data, or production dumps.
- Use environment variables with safe development defaults; fail closed in production.
- Do not add dependencies without a clear need; pin compatible ranges and update lockfiles when package manifests change.
- Add tests for behavior and security boundaries as domains are implemented.
- Do not claim a check passed unless it was actually run.
- Prefer small, reviewable commits and document consequential decisions.

## Workflow
1. Inspect existing code and conventions before changing files.
2. State assumptions and domain boundaries.
3. Implement the smallest coherent vertical slice.
4. Run formatting, lint, type, and test checks at the agreed verification stage.
5. Review diffs for secrets, permission leaks, missing migrations, and incomplete error handling.
