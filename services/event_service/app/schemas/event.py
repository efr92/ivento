from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, field_validator
from app.models.event import EventCategory, EventStatus


class LocationSchema(BaseModel):
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)
    address: Optional[str] = None


class EventCreateSchema(BaseModel):
    title: str = Field(min_length=3, max_length=200)
    description: Optional[str] = None
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)
    address: Optional[str] = None
    category: EventCategory = EventCategory.OTHER
    start_time: datetime
    end_time: Optional[datetime] = None
    max_participants: Optional[int] = Field(None, ge=2, le=10000)

    @field_validator("end_time")
    @classmethod
    def validate_end_time(cls, v, info):
        if v and "start_time" in info.data and v <= info.data["start_time"]:
            raise ValueError("end_time must be after start_time")
        return v


class EventUpdateSchema(BaseModel):
    title: Optional[str] = Field(None, min_length=3, max_length=200)
    description: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    max_participants: Optional[int] = None
    status: Optional[EventStatus] = None


class EventResponseSchema(BaseModel):
    id: int
    title: str
    description: Optional[str]
    latitude: float
    longitude: float
    address: Optional[str]
    category: EventCategory
    status: EventStatus
    start_time: datetime
    end_time: Optional[datetime]
    max_participants: Optional[int]
    current_participants: int
    creator_id: int
    created_at: datetime

    model_config = {"from_attributes": True}


class EventListSchema(BaseModel):
    items: list[EventResponseSchema]
    total: int
    page: int
    size: int


class NearbyEventsFilterSchema(BaseModel):
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)
    radius_km: float = Field(default=5.0, ge=0.1, le=100.0)
    category: Optional[EventCategory] = None
    status: Optional[EventStatus] = EventStatus.ACTIVE
    page: int = Field(default=1, ge=1)
    size: int = Field(default=20, ge=1, le=100)
