import json
import os
import urllib.request

import pytest

BASE_URL = os.getenv("XBOT_GATEWAY_URL")
pytestmark = pytest.mark.skipif(
    not BASE_URL, reason="Set XBOT_GATEWAY_URL to run live E2E tests."
)


def _post(path: str, payload: dict):
    req = urllib.request.Request(
        f"{BASE_URL}{path}",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    with urllib.request.urlopen(req, timeout=5) as response:
        return response.status, json.loads(response.read().decode("utf-8"))


def _get(path: str):
    with urllib.request.urlopen(f"{BASE_URL}{path}", timeout=5) as response:
        return json.loads(response.read().decode("utf-8"))


def test_order_requires_approval_then_can_be_rejected():
    status, create_payload = _post(
        "/v1/orders/create",
        {
            "market_id": "poly-pres-2028-win",
            "side": "buy",
            "quantity": 5,
            "limit_price": 0.57,
            "strategy_id": "hybrid_v1",
            "confidence": 0.8,
            "requires_approval": True
        }
    )
    assert status == 202
    assert create_payload["status"] == "pending_approval"

    pending = _get("/v1/approvals/pending")
    assert pending["count"] >= 1

    _, decision_payload = _post(
        "/v1/approvals/decision",
        {
            "approval_id": "approval_test",
            "request_id": create_payload["request_id"],
            "approved": False,
            "actor_id": "operator_test",
            "reason": "risk_check"
        }
    )
    assert decision_payload["status"] == "rejected"

