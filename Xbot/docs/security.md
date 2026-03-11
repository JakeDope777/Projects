# Security Baseline

## Auth and Access

- JWT-based API auth with short-lived access tokens.
- Role model scaffold: `admin`, `agent`, `viewer`.
- Approval-required order mode enabled by default.

## Secrets and Keys

- Secrets loaded from environment or secret manager.
- Trading hot-wallet key is isolated from treasury wallet.
- Ledger remains cold treasury custody.

## Risk Safety Controls

- Hard-stop on risk policy breach.
- Live autonomy blocked unless gate passes.
- Immutable JSONL decision ledger for event forensics.

## Next Hardening Steps

- MFA for dashboard operators.
- SSO and centralized policy enforcement.
- Secret rotation automation.
- Signed audit exports with integrity checks.

