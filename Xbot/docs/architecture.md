# Xbot Trading-First Architecture

## Topology

- **Local node (Mac mini):**
  - Execution worker (order loop).
  - Local OpenClow model adapter (optional).
  - Hot-wallet signer with strict wallet cap.
- **AWS control plane:**
  - API services.
  - Dashboard.
  - Postgres, Redis, object storage.
  - Observability and alerting.

## Services

- `gateway-api`: Auth, public API surface, websocket broadcaster.
- `trading-orchestrator`: Strategy lifecycle, approval-required mode, autonomy state.
- `ai-decision-service`: Multi-model routing and confidence scoring.
- `market-data-service`: Polymarket and external features ingestion.
- `execution-service`: Venue adapter dispatch and signed order handling.
- `risk-policy-service`: Editable presets and hard-stop checks.
- `portfolio-analytics-service`: Position state, PnL, and KPI aggregates.
- `worker-service`: Async jobs (replay, reports, backfills, evaluations).

## Persistence Model

- Primary state store: PostgreSQL (`POSTGRES_URL`) for orders, approvals, risk presets, positions, autonomy mode, and gate metrics.
- Fail-safe fallback: each service degrades to in-memory mode if PostgreSQL is unavailable.
- Immutable event trace: JSONL decision ledger for audit reconstruction.

## Event Envelope

All service bus events use:

- `event_id`
- `event_type` (`*.v1`)
- `correlation_id`
- `timestamp`
- `service`
- `policy_version`
- `payload`

## Autonomy Lifecycle

1. **approval_required** (launch default):
   - Signals can be generated.
   - Orders require explicit approval record.
2. **paper_autonomous**:
   - Continuous execution in paper mode.
3. **live_autonomous**:
   - Enabled after 30-day gate pass:
     - positive risk-adjusted return
     - drawdown under policy
     - zero critical violations
