from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
import os
from typing import Any

from fastapi import FastAPI
from pydantic import BaseModel, Field


class Side(str, Enum):
    buy = "buy"
    sell = "sell"


class DecisionRequest(BaseModel):
    market_id: str
    strategy_id: str = "hybrid_v1"
    context: dict[str, Any] = Field(default_factory=dict)


class DecisionResponse(BaseModel):
    side: Side
    confidence: float
    quantity: float
    limit_price: float
    rationale: str
    model_used: str
    created_at: str


app = FastAPI(title="xbot-ai-decision-service", version="0.1.0")

DecisionRequest.model_rebuild()
DecisionResponse.model_rebuild()


def _choose_model() -> str:
    if os.getenv("CLAUDE_API_KEY"):
        return "claude_latest"
    if os.getenv("OPENAI_API_KEY"):
        return "openai_fallback"
    if os.getenv("OPENCLAW_ENDPOINT"):
        return "openclaw_local"
    return "rules_only_fallback"


def _hybrid_decision(payload: DecisionRequest) -> DecisionResponse:
    context = payload.context
    momentum = float(context.get("momentum_score", 0.0))
    volatility = abs(float(context.get("volatility_score", 0.0)))
    price = float(context.get("mid_price", 0.5))
    available_capital = float(context.get("deployable_capital", 1000))

    side = Side.buy if momentum >= 0 else Side.sell
    confidence = max(0.05, min(0.99, 0.55 + momentum * 0.3 - volatility * 0.2))
    risk_scalar = max(0.2, min(1.0, 1.0 - volatility))
    position_budget = available_capital * 0.02 * risk_scalar
    quantity = max(1.0, round(position_budget / max(price, 0.01), 2))
    limit_price = round(price * (0.999 if side == Side.buy else 1.001), 4)

    model_used = _choose_model()
    rationale = (
        f"hybrid_rules_with_{model_used}: momentum={momentum:.3f}, "
        f"volatility={volatility:.3f}, risk_scalar={risk_scalar:.3f}"
    )

    return DecisionResponse(
        side=side,
        confidence=round(confidence, 4),
        quantity=quantity,
        limit_price=limit_price,
        rationale=rationale,
        model_used=model_used,
        created_at=datetime.now(tz=timezone.utc).isoformat()
    )


@app.get("/health")
def health() -> dict[str, Any]:
    return {
        "status": "healthy",
        "version": "0.1.0",
        "timestamp": datetime.now(tz=timezone.utc).isoformat(),
        "checks": {
            "model_router": "healthy"
        }
    }


@app.post("/v1/decision/generate", response_model=DecisionResponse)
def generate_decision(payload: DecisionRequest) -> DecisionResponse:
    return _hybrid_decision(payload)
