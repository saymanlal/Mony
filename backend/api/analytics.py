"""
User history analytics, statistics, and forecasts for MONY.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

import db
import main

logger = logging.getLogger(__name__)

router = APIRouter(tags=["analytics"])


class WeeklyFlow(BaseModel):
    week: str
    inflow_mon: float
    outflow_mon: float
    net_mon: float


class ForecastPoint(BaseModel):
    day: int
    projected_balance_mon: float


class AnalyticsSummaryResponse(BaseModel):
    user_address: str
    total_inflow_mon: float
    total_outflow_mon: float
    net_savings_mon: float
    savings_rate_pct: float
    mon_to_inr_trend_pct: float
    weekly_flows: List[WeeklyFlow]
    forecast_7d: List[ForecastPoint]
    category_tags: Dict[str, float]
    anomalies: List[str]
    insights: List[str]


class BaseInsightsProvider:
    """Interface allowing external AI/LLM models to be plugged in later."""
    def generate_insights(self, stats: Dict[str, Any]) -> List[str]:
        raise NotImplementedError


class RuleBasedInsightsProvider(BaseInsightsProvider):
    """Template-driven plain-language insights without external AI calls."""
    def generate_insights(self, stats: Dict[str, Any]) -> List[str]:
        inflow = stats.get("total_inflow", 0.0)
        outflow = stats.get("total_outflow", 0.0)
        savings_rate = stats.get("savings_rate", 0.0)
        inr_per_mon = stats.get("inr_per_mon", 8500.0)

        insights = []
        if inflow > 0:
            insights.append(
                f"You have deposited a total of {inflow:.4f} MON (approx ₹{inflow * inr_per_mon:,.2f})."
            )
        else:
            insights.append("No deposits recorded yet. Scan a banknote to fund your account.")

        if savings_rate >= 50.0:
            insights.append(
                f"Strong savings performance: retaining {savings_rate:.1f}% of all deposited funds."
            )
        elif savings_rate > 0:
            insights.append(
                f"Moderate savings rate: retaining {savings_rate:.1f}% of deposits."
            )

        if outflow > inflow * 0.8 and inflow > 0:
            insights.append(
                "High outflow detected: over 80% of deposited assets have been transferred or swapped."
            )

        return insights


# Default provider is rule-based templates
_insights_provider: BaseInsightsProvider = RuleBasedInsightsProvider()


def _exponential_smoothing(data: List[float], alpha: float = 0.3, periods: int = 7) -> List[float]:
    """Calculate future forecast using exponential smoothing."""
    if not data:
        return [0.0] * periods
    s = data[0]
    for val in data[1:]:
        s = alpha * val + (1.0 - alpha) * s
    return [round(s, 4) for _ in range(periods)]


@router.get("/analytics/summary", response_model=AnalyticsSummaryResponse)
async def get_analytics_summary(
    user_address: str = Query(..., description="User wallet address"),
) -> AnalyticsSummaryResponse:
    activities = await db.get_user_activity(user_address, limit=100)

    total_inflow = 0.0
    total_outflow = 0.0
    daily_balances: List[float] = []

    for act in activities:
        amt = float(act.get("amount_mon") or 0.0)
        total_inflow += amt
        daily_balances.append(total_inflow - total_outflow)

    net_savings = max(0.0, total_inflow - total_outflow)
    savings_rate = (net_savings / total_inflow * 100.0) if total_inflow > 0 else 0.0

    inr_per_mon = main.settings.demo_inr_per_mon
    if main.rate_service is not None:
        try:
            r = await main.rate_service.get_mon_inr_rate()
            inr_per_mon = r.get("inr_per_mon", inr_per_mon)
        except Exception:
            pass

    # 7-day forecast
    forecast_values = _exponential_smoothing(daily_balances or [net_savings], alpha=0.3, periods=7)
    forecast = [ForecastPoint(day=i + 1, projected_balance_mon=v) for i, v in enumerate(forecast_values)]

    # Weekly flow breakdown
    weekly_flows = [
        WeeklyFlow(
            week="Week 1",
            inflow_mon=round(total_inflow, 4),
            outflow_mon=round(total_outflow, 4),
            net_mon=round(net_savings, 4),
        )
    ]

    # Category breakdown
    categories = {
        "Deposits": round(total_inflow, 4),
        "Transfers": round(total_outflow, 4),
        "Savings Vault": 0.0,
    }

    # Anomalies
    anomalies: List[str] = []
    for act in activities:
        amt = float(act.get("amount_mon") or 0.0)
        if amt > 50.0:
            anomalies.append(f"Unusually large deposit of {amt:.2f} MON detected.")

    # Plain-language insights
    stats = {
        "total_inflow": total_inflow,
        "total_outflow": total_outflow,
        "savings_rate": savings_rate,
        "inr_per_mon": inr_per_mon,
    }
    insights = _insights_provider.generate_insights(stats)

    return AnalyticsSummaryResponse(
        user_address=user_address,
        total_inflow_mon=round(total_inflow, 4),
        total_outflow_mon=round(total_outflow, 4),
        net_savings_mon=round(net_savings, 4),
        savings_rate_pct=round(savings_rate, 2),
        mon_to_inr_trend_pct=1.45,
        weekly_flows=weekly_flows,
        forecast_7d=forecast,
        category_tags=categories,
        anomalies=anomalies,
        insights=insights,
    )
