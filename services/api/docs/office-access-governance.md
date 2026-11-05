# Nexora Office Access & Security Governance

## Authorization model

Every Office API request requires a valid Firebase-verified Nexora identity, active account, `is_staff=True`, verified email claim, and a recognized Office role. Browser-supplied roles are never trusted.

RBAC uses Django's built-in `auth.Group` membership on `NexoraUser`. Run `python manage.py seed_office_roles` to create the standard groups. The command does not assign users.

| Role | Portfolio | Audit log | Security events | Manage sessions | Manage access |
|---|---:|---:|---:|---:|
| Office Owner | Yes | Yes | Yes | Yes | Yes |
| Office Security Admin | No | No | Yes | Yes | Yes |
| Office Portfolio Manager | Yes | Yes | No | No | No |
| Office Auditor | No | Yes | Yes | No | No |
| Office Portfolio Viewer | Yes | No | No | No | No |

Superusers bypass the role matrix but still require an active staff account and verified email.

## Role assignment

Assign groups only through trusted Django Admin / internal operator workflow. Keep at least two separately controlled owner accounts for recovery; do not grant Owner to ordinary staff. This phase intentionally exposes no public role-assignment endpoint.

## Endpoints

- `GET /api/v1/office/access/me/`: current account roles and effective permissions.
- `GET /api/v1/office/access/security-events/`: paginated security event metadata; optional `event_type` and `user_id` filters.
- Session inventory and revocation endpoints are documented in `office-session-governance.md`; only Owner and Security Admin receive `sessions.manage`.

Security event responses omit credentials and token claims. IP address and user-agent are operationally sensitive; restrict this endpoint to Security Admin, Auditor, and Owner roles.

## Limitations

Django groups and application checks provide RBAC but do not make the database tamper-proof. Production deployments should protect Django Admin with MFA, network restrictions, secure backups, and monitored privileged access. Session revocation continues to use the existing Nexora identity session implementation.
