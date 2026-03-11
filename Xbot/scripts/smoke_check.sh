#!/usr/bin/env bash
set -euo pipefail

BASE_URL="${1:-http://localhost:4001}"

echo "[smoke] health"
curl -fsS "${BASE_URL}/health" >/dev/null

echo "[smoke] markets"
curl -fsS "${BASE_URL}/v1/markets" >/dev/null

echo "[smoke] autonomy mode"
curl -fsS "${BASE_URL}/v1/autonomy/mode" >/dev/null

echo "[smoke] risk presets"
curl -fsS "${BASE_URL}/v1/risk/presets" >/dev/null

echo "[smoke] analytics overview"
curl -fsS "${BASE_URL}/v1/analytics/overview" >/dev/null

echo "[smoke] ok"

