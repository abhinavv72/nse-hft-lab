from __future__ import annotations

from fastapi import APIRouter, Request


router = APIRouter(prefix="/api/metrics", tags=["metrics"])


@router.get("")
async def get_metrics(request: Request):
    services = request.app.state.services
    portfolio = services.portfolio.snapshot()
    return services.metrics.snapshot(portfolio)
