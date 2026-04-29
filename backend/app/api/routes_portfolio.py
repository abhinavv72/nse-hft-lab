from __future__ import annotations

from fastapi import APIRouter, Request


router = APIRouter(prefix="/api/portfolio", tags=["portfolio"])


@router.get("")
async def get_portfolio(request: Request):
    return request.app.state.services.portfolio.snapshot()
