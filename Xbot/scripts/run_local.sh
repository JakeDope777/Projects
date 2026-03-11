#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

echo "[xbot] starting infra dependencies"
docker compose up -d postgres redis minio

echo "[xbot] install JS dependencies"
npm install

echo "[xbot] start node services"
npm run dev:risk &
npm run dev:execution &
npm run dev:analytics &
npm run dev:orchestrator &
npm run dev:gateway &
npm run dev:worker &
npm run dev:dashboard &

echo "[xbot] start python services"
python3 -m venv .venv
source .venv/bin/activate
pip install -r apps/ai-decision-service/requirements.txt
pip install -r apps/market-data-service/requirements.txt
uvicorn app.main:app --app-dir apps/ai-decision-service --host 0.0.0.0 --port 8001 &
uvicorn app.main:app --app-dir apps/market-data-service --host 0.0.0.0 --port 8002 &

echo "[xbot] all services launched"
