# Xbot Trading-First Platform

Xbot is a trading-first autonomous bot platform designed for internal use with a hybrid runtime:

- Local execution node on Mac mini for continuous strategy and order handling.
- AWS control plane for API, dashboard, analytics, and persistence.
- Polymarket-first execution with pluggable venue adapters.

## Monorepo Layout

- `apps/gateway-api`: Public REST/WebSocket API.
- `apps/trading-orchestrator`: Strategy orchestration and autonomy flow.
- `apps/execution-service`: Venue execution abstraction and Polymarket adapter.
- `apps/risk-policy-service`: Risk preset and policy evaluation service.
- `apps/portfolio-analytics-service`: PnL and portfolio analytics.
- `apps/worker-service`: Queue workers for async processing.
- `apps/dashboard`: Next.js operator dashboard.
- `apps/ai-decision-service`: FastAPI model routing and decision support.
- `apps/market-data-service`: FastAPI market and feature aggregation.
- `packages/shared-*`: Cross-service contracts, events, and risk logic.
- `infra/`: Docker, Kubernetes, and Terraform starter assets.
- `docs/`: Architecture and operations documentation.

## Key Defaults

- Launch mode: `approval_required`.
- Autonomy gate: 30-day pass with risk-adjusted return and zero critical violations.
- Conservative risk preset:
  - Max per-market exposure: 2%
  - Max total open exposure: 15%
  - Max daily loss: 1.5%
  - Max concurrent positions: 3
  - Hard halt on breach

## Quick Start

1. Copy `.env.example` to `.env` and set secrets.
2. Start infra dependencies with Docker Compose.
3. Install JS dependencies with `npm install`.
4. Create Python virtual envs for `ai-decision-service` and `market-data-service`.
5. Run services:
   - `npm run dev:gateway`
   - `npm run dev:orchestrator`
   - `npm run dev:execution`
   - `npm run dev:risk`
   - `npm run dev:analytics`
   - `npm run dev:worker`
   - `npm run dev:dashboard`
   - `uvicorn app.main:app --app-dir apps/ai-decision-service --port 8001`
   - `uvicorn app.main:app --app-dir apps/market-data-service --port 8002`
6. Run smoke checks:
   - `./scripts/smoke_check.sh`

## Verification

- JS type checks: `npm run typecheck`
- JS tests: `npm test`
- Python tests: `python3 -m pytest apps/ai-decision-service/tests apps/market-data-service/tests tests/integration tests/e2e -q`

## Status

This implementation establishes a production-oriented baseline with:

- Versioned event envelope (`*.v1`) and contract schemas.
- Full v1 endpoint surfaces and service stubs.
- Risk policy engine, approval flow hooks, and autonomy gate evaluator.
- Polymarket-first execution adapter interface with live-safe guardrails.
- Unit/integration starter tests and deployment scaffolding.
