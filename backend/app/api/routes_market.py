from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel


router = APIRouter(prefix="/api/market", tags=["market"])


def services(request: Request):
    return request.app.state.services


class MarketStartRequest(BaseModel):
    speed: int = 1
    mode: str = "live"


class SymbolRequest(BaseModel):
    symbol: str


@router.get("/state")
async def get_state(request: Request):
    return services(request).simulator.dashboard_state()


@router.get("/ipo/current")
async def get_current_ipos(request: Request):
    try:
        return await services(request).ipo.current_issues()
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=503, detail="Official NSE IPO data is temporarily unavailable") from exc


@router.post("/start")
async def start_market(payload: MarketStartRequest, request: Request):
    return await services(request).simulator.start_market(speed=payload.speed, mode=payload.mode)


@router.post("/stop")
async def stop_market(request: Request):
    return await services(request).simulator.stop_market()


@router.post("/reset")
async def reset_market(request: Request):
    return await services(request).simulator.reset_session()


@router.post("/volatility-spike")
async def volatility_spike(request: Request):
    return await services(request).simulator.inject_volatility_spike()


@router.post("/select-symbol")
async def select_symbol(payload: SymbolRequest, request: Request):
    return await services(request).simulator.select_symbol(payload.symbol)
