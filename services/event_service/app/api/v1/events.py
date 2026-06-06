from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from app.db.session import get_db
from app.schemas.event import (
    EventCreateSchema,
    EventUpdateSchema,
    EventResponseSchema,
    EventListSchema,
    NearbyEventsFilterSchema
)
from app.schemas.comment import CommentCreateSchema
from app.services.event_service import EventService
from app.kafka.producer import get_kafka_producer, KafkaProducer
from app.core.dependencies import get_current_user
from app.models.event import EventCategory, EventStatus

router = APIRouter(prefix="/events", tags=["events"])


def get_event_service(
    db: AsyncSession = Depends(get_db),
    kafka: KafkaProducer = Depends(get_kafka_producer)
) -> EventService:
    return EventService(db, kafka)


@router.get("/nearby", response_model=EventListSchema)
async def get_nearby_events(
    latitude: float = Query(..., ge=-90, le=90),
    longitude: float = Query(..., ge=-180, le=180),
    radius_km: float = Query(default=5.0, ge=0.1, le=100.0),
    category: Optional[EventCategory] = None,
    status: Optional[EventStatus] = EventStatus.ACTIVE,
    page: int = Query(default=1, ge=1),
    size: int = Query(default=20, ge=1, le=100),
    service: EventService = Depends(get_event_service)
):
    filters = NearbyEventsFilterSchema(
        latitude=latitude,
        longitude=longitude,
        radius_km=radius_km,
        category=category,
        status=status,
        page=page,
        size=size
    )
    return await service.get_nearby_events(filters)


@router.post("", response_model=EventResponseSchema, status_code=201)
async def create_event(
    data: EventCreateSchema,
    current_user: dict = Depends(get_current_user),
    service: EventService = Depends(get_event_service)
):
    return await service.create_event(data, current_user["user_id"])


@router.get("/{event_id}", response_model=EventResponseSchema)
async def get_event(
    event_id: int,
    service: EventService = Depends(get_event_service)
):
    return await service.get_event(event_id)


@router.patch("/{event_id}", response_model=EventResponseSchema)
async def update_event(
    event_id: int,
    data: EventUpdateSchema,
    current_user: dict = Depends(get_current_user),
    service: EventService = Depends(get_event_service)
):
    return await service.update_event(event_id, data, current_user["user_id"])


@router.post("/{event_id}/join")
async def join_event(
    event_id: int,
    current_user: dict = Depends(get_current_user),
    service: EventService = Depends(get_event_service)
):
    return await service.join_event(event_id, current_user["user_id"])


@router.delete("/{event_id}/leave")
async def leave_event(
    event_id: int,
    current_user: dict = Depends(get_current_user),
    service: EventService = Depends(get_event_service)
):
    return await service.leave_event(event_id, current_user["user_id"])


@router.post("/{event_id}/comments", status_code=201)
async def add_comment(
    event_id: int,
    data: CommentCreateSchema,
    current_user: dict = Depends(get_current_user),
    service: EventService = Depends(get_event_service)
):
    return await service.add_comment(
        event_id, data,
        current_user["user_id"],
        current_user["username"]
    )


@router.get("/{event_id}/comments")
async def get_comments(
    event_id: int,
    page: int = Query(default=1, ge=1),
    size: int = Query(default=50, ge=1, le=200),
    service: EventService = Depends(get_event_service)
):
    event = await service.get_event(event_id)
    comments = event.comments
    start = (page - 1) * size
    return {
        "items": comments[start:start + size],
        "total": len(comments)
    }
