from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from fastapi import FastAPI

app = FastAPI(title="xbot-market-data-service", version="0.1.0")


def _sample_markets() -> list[dict[str, Any]]:
    return [
        {
            "id": "poly-pres-2028-win",
            "title": "Will candidate X win the 2028 election?",
            "mid_price": 0.57,
            "liquidity": 120000,
            "volume_24h": 84000
        },
        {
            "id": "poly-btc-100k-2026",
            "title": "Will BTC hit 100k by end of 2026?",
            "mid_price": 0.41,
            "liquidity": 95000,
            "volume_24h": 47000
        }
    ]


@app.get("/health")
def health() -> dict[str, Any]:
    return {
        "status": "healthy",
        "version": "0.1.0",
        "timestamp": datetime.now(tz=timezone.utc).isoformat(),
        "checks": {
            "market_feeds": "healthy"
        }
    }


@app.get("/v1/markets")
def list_markets() -> dict[str, Any]:
    return {
        "count": len(_sample_markets()),
        "items": _sample_markets(),
        "timestamp": datetime.now(tz=timezone.utc).isoformat()
    }


@app.get("/v1/markets/{market_id}/orderbook")
def orderbook(market_id: str) -> dict[str, Any]:
    return {
        "market_id": market_id,
        "bids": [[0.56, 2500], [0.55, 4600]],
        "asks": [[0.58, 2200], [0.59, 3800]],
        "timestamp": datetime.now(tz=timezone.utc).isoformat()
    }


@app.get("/v1/features/{market_id}")
def market_features(market_id: str) -> dict[str, Any]:
    return {
        "market_id": market_id,
        "features": {
            "momentum_score": 0.22,
            "volatility_score": 0.18,
            "sentiment_score": 0.11,
            "onchain_flow_score": 0.04,
            "news_impact_score": 0.06
        },
        "sources": ["polymarket", "news", "social", "onchain"],
        "timestamp": datetime.now(tz=timezone.utc).isoformat()
    }

