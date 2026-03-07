"""
Token Accounting Service

Tracks token consumption per user and per module.
Deducts tokens from user balances and enforces limits.
"""

from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.orm import Session

from ..db import models


# Default token costs per operation
TOKEN_COSTS = {
    "chat": 10,
    "business_analysis": 50,
    "creative_design": 30,
    "crm_campaign": 20,
    "analytics_reporting": 25,
    "integrations": 5,
    "memory": 2,
    "system": 0,
    "general": 10,
}


class TokenAccountingService:
    """Manages token balances, usage logging, and tier enforcement."""

    def __init__(self, db: Session):
        self.db = db

    def get_balance(self, user_id: str) -> Optional[models.TokenAccount]:
        """Retrieve the token account for a user."""
        return (
            self.db.query(models.TokenAccount)
            .filter(models.TokenAccount.user_id == user_id)
            .first()
        )

    def has_sufficient_tokens(self, user_id: str, module_name: str) -> bool:
        """Check whether the user has enough tokens for the requested operation."""
        account = self.get_balance(user_id)
        if account is None:
            return False
        cost = TOKEN_COSTS.get(module_name, 10)
        return account.balance >= cost

    def deduct_tokens(
        self, user_id: str, module_name: str, tokens_used: Optional[int] = None
    ) -> dict:
        """
        Deduct tokens from the user's balance and log the usage.

        Args:
            user_id: The user whose balance to deduct from.
            module_name: The module that consumed the tokens.
            tokens_used: Override the default cost if provided.

        Returns:
            Dict with status, remaining balance, and tokens deducted.
        """
        account = self.get_balance(user_id)
        if account is None:
            return {"status": "error", "message": "Token account not found"}

        cost = tokens_used if tokens_used is not None else TOKEN_COSTS.get(module_name, 10)

        if account.balance < cost:
            return {
                "status": "insufficient_tokens",
                "balance": account.balance,
                "required": cost,
                "message": "Insufficient tokens. Please upgrade your plan or purchase more tokens.",
            }

        account.balance -= cost

        # Log the usage
        log_entry = models.UsageLog(
            user_id=user_id,
            module_name=module_name,
            tokens_used=cost,
        )
        self.db.add(log_entry)
        self.db.commit()

        return {
            "status": "success",
            "tokens_deducted": cost,
            "remaining_balance": account.balance,
        }

    def get_usage_summary(self, user_id: str, days: int = 30) -> dict:
        """
        Get a summary of token usage for a user over a period.

        Args:
            user_id: The user to query.
            days: Number of days to look back.

        Returns:
            Dict with usage breakdown by module and totals.
        """
        from datetime import timedelta

        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        logs = (
            self.db.query(models.UsageLog)
            .filter(
                models.UsageLog.user_id == user_id,
                models.UsageLog.timestamp >= cutoff,
            )
            .all()
        )

        by_module: dict[str, int] = {}
        total = 0
        for log in logs:
            by_module[log.module_name] = by_module.get(log.module_name, 0) + log.tokens_used
            total += log.tokens_used

        account = self.get_balance(user_id)

        return {
            "user_id": user_id,
            "period_days": days,
            "total_tokens_used": total,
            "usage_by_module": by_module,
            "current_balance": account.balance if account else 0,
            "tier": account.tier if account else "unknown",
        }

    def reset_free_tier_balances(self) -> int:
        """
        Reset token balances for all free-tier users.
        Called at the start of each billing period.

        Returns:
            Number of accounts reset.
        """
        from ..core.config import settings

        accounts = (
            self.db.query(models.TokenAccount)
            .filter(models.TokenAccount.tier == "free")
            .all()
        )
        count = 0
        for account in accounts:
            account.balance = settings.FREE_TIER_MONTHLY_TOKENS
            account.reset_date = datetime.now(timezone.utc)
            count += 1
        self.db.commit()
        return count
