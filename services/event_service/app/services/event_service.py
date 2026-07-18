import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from sqlalchemy.orm import selectinload
from fastapi import HTTPException, status

from app.models.event import Event, EventParticipant, EventStatus
from app.models.comment import Comment
from app.schemas.event import (
    EventCreateSchema,
    EventUpdateSchema,
    EventResponseSchema,
    NearbyEventsFilterSchema
)
from app.schemas.comment import CommentCreateSchema
from app.kafka.producer import KafkaProducer
from app.lang.messages import MESSAGES
from app.services.geo_service import GeoService
from shared.kafka_topics import KafkaTopics

logger = logging.getLogger(__name__)


class EventService:
    def __init__(self, db: AsyncSession, kafka: KafkaProducer):
        self.db = db
        self.kafka = kafka
        self.geo = GeoService()

    async def create_event(
        self,
        data: EventCreateSchema,
        creator_id: int
    ) -> EventResponseSchema:
        event = Event(
            **data.model_dump(),
            creator_id=creator_id
        )
        self.db.add(event)
        await self.db.commit()
        await self.db.refresh(event)

        await self.kafka.send(
            topic=KafkaTopics.EVENT_CREATED,
            value={
                "event_id": event.id,
                "title": event.title,
                "creator_id": creator_id,
                "category": event.category.value,
                "latitude": event.latitude,
                "longitude": event.longitude,
                "start_time": event.start_time.isoformat()
            },
            key=str(event.id)
        )

        logger.info(f"Event {event.id} created by user {creator_id}")
        return EventResponseSchema.model_validate(event)

    async def get_nearby_events(
        self,
        filters: NearbyEventsFilterSchema
    ) -> dict:
        min_lat, max_lat, min_lon, max_lon = self.geo.get_bounding_box(
            filters.latitude, filters.longitude, filters.radius_km
        )

        conditions = [
            Event.latitude.between(min_lat, max_lat),
            Event.longitude.between(min_lon, max_lon),
        ]

        if filters.status:
            conditions.append(Event.status == filters.status)
        if filters.category:
            conditions.append(Event.category == filters.category)

        query = select(Event).where(and_(*conditions))
        result = await self.db.execute(query)
        all_events = result.scalars().all()

        nearby_events = [
            event for event in all_events
            if self.geo.haversine_distance(
                filters.latitude, filters.longitude,
                event.latitude, event.longitude
            ) <= filters.radius_km
        ]

        total = len(nearby_events)
        start = (filters.page - 1) * filters.size
        end = start + filters.size
        paginated = nearby_events[start:end]

        return {
            "items": [EventResponseSchema.model_validate(e) for e in paginated],
            "total": total,
            "page": filters.page,
            "size": filters.size
        }

    async def get_event(self, event_id: int) -> Event:
        result = await self.db.execute(
            select(Event)
            .options(selectinload(Event.comments), selectinload(Event.participants))
            .where(Event.id == event_id)
        )
        event = result.scalar_one_or_none()
        if not event:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=MESSAGES["event_not_found"].format(event_id=event_id)
            )
        return event

    async def update_event(
        self,
        event_id: int,
        data: EventUpdateSchema,
        user_id: int
    ) -> EventResponseSchema:
        event = await self.get_event(event_id)

        if event.creator_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=MESSAGES["only_creator_can_update"]
            )

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(event, field, value)

        await self.db.commit()
        await self.db.refresh(event)

        await self.kafka.send(
            topic=KafkaTopics.EVENT_UPDATED,
            value={"event_id": event.id, "updated_fields": list(update_data.keys())},
            key=str(event.id)
        )

        return EventResponseSchema.model_validate(event)

    async def join_event(self, event_id: int, user_id: int) -> dict:
        event = await self.get_event(event_id)

        if event.status != EventStatus.ACTIVE:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=MESSAGES["cannot_join_inactive"]
            )

        if event.max_participants and event.current_participants >= event.max_participants:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=MESSAGES["event_is_full"]
            )

        existing = await self.db.execute(
            select(EventParticipant).where(
                and_(
                    EventParticipant.event_id == event_id,
                    EventParticipant.user_id == user_id
                )
            )
        )
        if existing.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=MESSAGES["already_joined"]
            )

        participant = EventParticipant(event_id=event_id, user_id=user_id)
        self.db.add(participant)
        event.current_participants += 1
        await self.db.commit()

        await self.kafka.send(
            topic=KafkaTopics.USER_JOINED_EVENT,
            value={
                "event_id": event_id,
                "user_id": user_id,
                "creator_id": event.creator_id,
                "event_title": event.title
            },
            key=str(event_id)
        )

        return {"message": MESSAGES["joined_successfully"]}

    async def leave_event(self, event_id: int, user_id: int) -> dict:
        event = await self.get_event(event_id)

        result = await self.db.execute(
            select(EventParticipant).where(
                and_(
                    EventParticipant.event_id == event_id,
                    EventParticipant.user_id == user_id
                )
            )
        )
        participant = result.scalar_one_or_none()

        if not participant:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=MESSAGES["not_a_participant"]
            )

        await self.db.delete(participant)
        event.current_participants = max(0, event.current_participants - 1)
        await self.db.commit()

        await self.kafka.send(
            topic=KafkaTopics.USER_LEFT_EVENT,
            value={"event_id": event_id, "user_id": user_id},
            key=str(event_id)
        )

        return {"message": MESSAGES["left_successfully"]}

    async def add_comment(
        self,
        event_id: int,
        data: CommentCreateSchema,
        user_id: int,
        username: str
    ) -> dict:
        await self.get_event(event_id)

        comment = Comment(
            event_id=event_id,
            user_id=user_id,
            username=username,
            text=data.text,
            parent_id=data.parent_id
        )
        self.db.add(comment)
        await self.db.commit()
        await self.db.refresh(comment)

        await self.kafka.send(
            topic=KafkaTopics.COMMENT_CREATED,
            value={
                "comment_id": comment.id,
                "event_id": event_id,
                "user_id": user_id,
                "username": username
            },
            key=str(event_id)
        )

        return {
            "id": comment.id,
            "text": comment.text,
            "username": comment.username,
            "created_at": comment.created_at.isoformat()
        }
