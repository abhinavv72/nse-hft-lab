from __future__ import annotations

from fastapi import APIRouter, Request
from pydantic import BaseModel


router = APIRouter(prefix="/api/risk", tags=["risk"])


def services(request: Request):
    return request.app.state.services


class LimitsPayload(BaseModel):
    max_order_qty: int | None = None
    max_position_per_symbol: int | None = None
    max_daily_loss: float | None = None
    max_price_deviation_bps: float | None = None
    stale_market_ms: int | None = None

    def compact(self) -> dict:
        return {key: value for key, value in self.model_dump().items() if value is not None}


class KillSwitchPayload(BaseModel):
    enabled: bool


@router.get("")
async def get_risk(request: Request):
    return services(request).risk.snapshot()


@router.post("/limits")
async def update_limits(payload: LimitsPayload, request: Request):
    return services(request).risk.update_limits(payload.compact())


@router.post("/kill-switch")
async def set_kill_switch(payload: KillSwitchPayload, request: Request):
    services(request).risk.set_kill_switch(payload.enabled)
    return services(request).risk.snapshot()
