# Xbot Operations Runbook

## Launch Sequence

1. Confirm risk preset is conservative and hot-wallet balance is within cap.
2. Start all services and verify `/health`.
3. Keep autonomy mode as `approval_required`.
4. Review pending approvals in dashboard before each execution.

## Incident Controls

- **Hard halt:** set autonomy mode to `halted`.
- **Kill switch:** stop `execution-service` and `worker-service`.
- **Risk breach:** reject pending approvals and lock new order submission.

## 30-Day Autonomy Gate

Promotion from `approval_required` to `live_autonomous` requires:

- At least 30-day evaluation window.
- Positive cumulative return.
- Sharpe-like ratio above threshold.
- Max drawdown inside active risk cap.
- Zero critical policy violations.

## Custody Model

- Ledger remains treasury/cold storage.
- Bot uses capped hot wallet for continuous execution.
- Refill flow is manual and audited.

