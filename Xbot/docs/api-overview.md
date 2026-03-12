# API Overview (v1)

Base URL (Gateway): `http://localhost:4001`

## Auth

- `POST /v1/auth/login`
- `POST /v1/auth/refresh`

## Markets

- `GET /v1/markets`
- `GET /v1/markets/:marketId/orderbook`
- `GET /v1/markets/:marketId/features`

## Signals and Orders

- `POST /v1/signals/generate`
- `POST /v1/orders/create`
- `POST /v1/orders/cancel`
- `GET /v1/orders/:requestId`

## Portfolio and Analytics

- `GET /v1/positions`
- `GET /v1/portfolio/pnl`
- `GET /v1/analytics/overview`

## Risk and Autonomy

- `GET /v1/risk/policies`
- `GET /v1/risk/presets`
- `PUT /v1/risk/presets/:name`
- `GET /v1/autonomy/mode`
- `PUT /v1/autonomy/mode`
- `GET /v1/autonomy/gate`

## Approvals

- `GET /v1/approvals/pending`
- `POST /v1/approvals/decision`
