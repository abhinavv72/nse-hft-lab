from __future__ import annotations

from fastapi import APIRouter, Request


router = APIRouter(prefix="/api/news", tags=["news"])


def services(request: Request):
    return request.app.state.services


@router.get("")
async def get_news(request: Request):
    return {"articles": services(request).news.latest()}


@router.post("/refresh")
async def refresh_news(request: Request):
    added = await services(request).simulator.refresh_news()
    return {"added": len(added), "articles": services(request).news.latest()}
