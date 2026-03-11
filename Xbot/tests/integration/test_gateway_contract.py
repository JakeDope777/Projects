import json
import os
import urllib.request

import pytest

BASE_URL = os.getenv("XBOT_GATEWAY_URL")
pytestmark = pytest.mark.skipif(
    not BASE_URL, reason="Set XBOT_GATEWAY_URL to run live integration tests."
)


def _get(path: str):
    with urllib.request.urlopen(f"{BASE_URL}{path}", timeout=5) as response:
        return json.loads(response.read().decode("utf-8"))


def _post(path: str, payload: dict):
    req = urllib.request.Request(
        f"{BASE_URL}{path}",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    with urllib.request.urlopen(req, timeout=5) as response:
        return response.status, json.loads(response.read().decode("utf-8"))


def test_health_contract():
    payload = _get("/health")
    assert payload["status"] in {"healthy", "degraded", "unhealthy"}
    assert "checks" in payload


def test_login_contract():
    _, payload = _post(
        "/v1/auth/login",
        {"email": "operator@xbot.local", "password": "StrongPass!123"}
    )
    assert "access_token" in payload
    assert payload["user"]["role"] == "admin"

