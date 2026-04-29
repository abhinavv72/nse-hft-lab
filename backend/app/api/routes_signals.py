from __future__ import annotations

from fastapi import APIRouter, Request


router = APIRouter(prefix="/api/signals", tags=["signals"])


def services(request: Request):
    return request.app.state.services


@router.get("")
async def get_signals(request: Request):
    return {"signals": services(request).signals.latest()}
