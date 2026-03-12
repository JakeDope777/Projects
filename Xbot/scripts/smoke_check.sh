#!/usr/bin/env bash
set -euo pipefail

BASE_URL="${1:-http://localhost:4001}"
OPERATOR_EMAIL="${XBOT_OPERATOR_EMAIL:-operator@xbot.local}"
OPERATOR_PASSWORD="${XBOT_OPERATOR_PASSWORD:-ChangeMe!123}"

echo "[smoke] health"
curl -fsS "${BASE_URL}/health" >/dev/null

echo "[smoke] login"
TOKEN="$(
  curl -fsS "${BASE_URL}/v1/auth/login" \
    -H "Content-Type: application/json" \
    -d "{\"email\":\"${OPERATOR_EMAIL}\",\"password\":\"${OPERATOR_PASSWORD}\"}" \
  | python3 -c 'import json,sys; print(json.load(sys.stdin)["access_token"])'
)"

echo "[smoke] markets"
curl -fsS "${BASE_URL}/v1/markets" \
  -H "Authorization: Bearer ${TOKEN}" >/dev/null

echo "[smoke] autonomy mode"
curl -fsS "${BASE_URL}/v1/autonomy/mode" \
  -H "Authorization: Bearer ${TOKEN}" >/dev/null

echo "[smoke] risk presets"
curl -fsS "${BASE_URL}/v1/risk/presets" \
  -H "Authorization: Bearer ${TOKEN}" >/dev/null

echo "[smoke] analytics overview"
curl -fsS "${BASE_URL}/v1/analytics/overview" \
  -H "Authorization: Bearer ${TOKEN}" >/dev/null

echo "[smoke] ok"
