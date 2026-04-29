from __future__ import annotations

from fastapi import APIRouter, Request
from pydantic import BaseModel


router = APIRouter(prefix="/api/replay", tags=["replay"])


def services(request: Request):
    return request.app.state.services


class ReplayStartRequest(BaseModel):
    session_id: str
    speed: int = 5


@router.get("/sessions")
async def list_sessions(request: Request):
    return {"sessions": services(request).replay.list_sessions()}


@router.post("/start")
async def start_replay(payload: ReplayStartRequest, request: Request):
    return await services(request).simulator.start_market(speed=payload.speed, mode="replay", replay_session_id=payload.session_id)


@router.post("/export")
async def export_session(request: Request):
    session_id = services(request).simulator.session.session_id
    return services(request).persistence.export_session(session_id)
