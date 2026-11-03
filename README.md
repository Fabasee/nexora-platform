# Nexora Platform

A modular, service-ready foundation for the Nexora multi-product ecosystem.

> Public repository: never commit credentials, private keys, production environment files, service-account JSON, or user data.

## Stack

- Mobile: React Native, Expo, Expo Router, TypeScript
- API: Django and Django REST Framework
- Cloud integrations: Firebase behind replaceable infrastructure adapters
- Architecture: Modular Monolith → Service-Ready

## Core principles

1. One Nexora identity does not imply shared access to every product's data.
2. Product domains own their data and authorization policies.
3. Domain and application layers remain provider-neutral; Firebase SDKs belong in infrastructure adapters.
4. Default-deny authorization, validated inputs, audit trails, and secret-free source control.
5. Build a coherent platform foundation before introducing individual products.
6. Keep infrastructure replaceable and test boundaries explicitly.

## Planned layout

```text
apps/mobile/             Expo Router application
services/api/            Django REST API
infra/firebase/          Security rules and safe Firebase configuration
docs/architecture/       System design and architecture decisions
docs/security/           Threat model and security standards
docs/development/        Local setup and contribution workflow
```

## Initial delivery scope

- Mobile application shell and typed navigation
- Django API foundation and health endpoint
- Provider-neutral identity and authentication contracts
- Firebase adapter boundary (no credentials committed)
- API error, pagination, logging, and request-correlation conventions
- CI and developer documentation

## Security

Firebase client configuration is not authorization. Enforce access control in trusted backend services and Firebase Security Rules. Never publish Admin SDK credentials or disable App Check as a shortcut.

## Project status

Repository initialization in progress.
