# ADR 0001: Modular Monolith First

- Status: Accepted
- Decision: Start with a modular Django monolith and explicit domain/application/infrastructure boundaries.
- Context: Nexora needs shared platform capabilities without coupling independent products or creating premature distributed-system complexity.
- Consequences: Domain ownership and contracts are explicit; extraction into services remains possible when scale or team boundaries justify it. Avoid cross-domain database shortcuts and vendor imports in domain logic.
