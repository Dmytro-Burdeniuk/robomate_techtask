from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, distinct, cast, Date
from datetime import date, timedelta
from typing import List
import uuid

from .db import get_db
from .models import Event
from .schemas import EventSchema
from .auth import get_api_key
from .ratelimiter import rl
from .rabbitmq import publish_to_queue


router = APIRouter()


@router.post("/events")
async def ingest_events(
    events: List[EventSchema],
    api_key: str = Depends(get_api_key),
):
    ok = await rl.allow("global")
    if not ok:
        raise HTTPException(status_code=429, detail="Rate limit exceeded")

    await publish_to_queue(events)

    return {"ok": True, "queued": len(events)}


@router.get("/stats/dau")
async def get_dau(
    from_date: date = Query(..., alias="from"),
    to_date: date = Query(..., alias="to"),
    db: Session = Depends(get_db),
    api_key: str = Depends(get_api_key),
):
    rows = (
        db.query(
            cast(Event.occurred_at, Date).label("day"),
            func.count(distinct(Event.user_id)).label("unique_users"),
        )
        .filter(Event.occurred_at >= from_date)
        .filter(Event.occurred_at <= to_date)
        .group_by("day")
        .order_by("day")
        .all()
    )

    data = [{"date": r.day.isoformat(), "unique_users": r.unique_users} for r in rows]
    return {"from": str(from_date), "to": str(to_date), "dau": data}


@router.get("/stats/top-events")
async def get_top_events(
    from_date: date = Query(..., alias="from"),
    to_date: date = Query(..., alias="to"),
    limit: int = 10,
    db: Session = Depends(get_db),
    api_key: str = Depends(get_api_key),
):
    rows = (
        db.query(Event.event_type, func.count(Event.event_id).label("count"))
        .filter(Event.occurred_at >= from_date)
        .filter(Event.occurred_at <= to_date)
        .group_by(Event.event_type)
        .order_by(func.count(Event.event_id).desc())
        .limit(limit)
        .all()
    )
    data = [{"event_type": r.event_type, "count": r.count} for r in rows]
    return {
        "from": str(from_date),
        "to": str(to_date),
        "limit": limit,
        "top_events": data,
    }


@router.get("/stats/retention")
async def get_retention(
    start_date: date,
    windows: int = 3,
    db: Session = Depends(get_db),
    api_key: str = Depends(get_api_key),
):
    retention = []
    for i in range(windows):
        day_start = start_date + timedelta(days=i)
        day_end = day_start + timedelta(days=1)
        user_count = (
            db.query(func.count(distinct(Event.user_id)))
            .filter(Event.occurred_at >= day_start)
            .filter(Event.occurred_at < day_end)
            .scalar()
        )
        retention.append({"date": day_start.isoformat(), "unique_users": user_count})

    return {
        "start_date": str(start_date),
        "windows": windows,
        "type": "daily",
        "retention": retention,
    }
