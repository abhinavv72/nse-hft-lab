from __future__ import annotations

from fastapi import APIRouter, Request
from pydantic import BaseModel


router = APIRouter(prefix="/api/strategy", tags=["strategy"])


def services(request: Request):
    return request.app.state.services


class StrategyPayload(BaseModel):
    symbol: str | None = None
    spread_bps: float | None = None
    qty: int | None = None
    aggression: float | None = None
    threshold_bps: float | None = None
    window: int | None = None

    def compact(self) -> dict:
        return {key: value for key, value in self.model_dump().items() if value is not None}


@router.get("")
async def list_strategies(request: Request):
    return services(request).strategy.snapshot()


@router.post("/start/{strategy_id}")
async def start_strategy(strategy_id: str, payload: StrategyPayload, request: Request):
    return await services(request).strategy.start(strategy_id, payload.compact())


@router.post("/stop/{strategy_id}")
async def stop_strategy(strategy_id: str, request: Request):
    return await services(request).strategy.stop(services(request).simulator.session.session_id, strategy_id)


@router.post("/config/{strategy_id}")
async def update_strategy(strategy_id: str, payload: StrategyPayload, request: Request):
    return await services(request).strategy.update(strategy_id, payload.compact())
