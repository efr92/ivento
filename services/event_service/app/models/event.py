from datetime import datetime
from typing import Optional
from sqlalchemy import (
    String, Text, Float, Integer, DateTime,
    ForeignKey, Enum, func, Index
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base
import enum


class EventCategory(str, enum.Enum):
    SPORT = "sport"
    MUSIC = "music"
    COMMUNITY = "community"
    EDUCATION = "education"
    ENTERTAINMENT = "entertainment"
    OTHER = "other"


class EventStatus(str, enum.Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    ONGOING = "ongoing"
    FINISHED = "finished"
    CANCELLED = "cancelled"


class Event(Base):
    __tablename__ = "events"
    __table_args__ = (
        Index("idx_events_location", "latitude", "longitude"),
        Index("idx_events_status_category", "status", "category"),
        Index("idx_events_start_time", "start_time"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)

    latitude: Mapped[float] = mapped_column(Float, nullable=False)
    longitude: Mapped[float] = mapped_column(Float, nullable=False)
    address: Mapped[Optional[str]] = mapped_column(String(500))

    category: Mapped[EventCategory] = mapped_column(
        Enum(EventCategory), default=EventCategory.OTHER
    )
    status: Mapped[EventStatus] = mapped_column(
        Enum(EventStatus), default=EventStatus.ACTIVE
    )

    start_time: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    end_time: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    max_participants: Mapped[Optional[int]] = mapped_column(Integer)
    current_participants: Mapped[int] = mapped_column(Integer, default=0)

    creator_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    comments: Mapped[list["Comment"]] = relationship(
        "Comment", back_populates="event", cascade="all, delete-orphan"
    )
    participants: Mapped[list["EventParticipant"]] = relationship(
        "EventParticipant", back_populates="event", cascade="all, delete-orphan"
    )


class EventParticipant(Base):
    __tablename__ = "event_participants"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    event_id: Mapped[int] = mapped_column(
        ForeignKey("events.id", ondelete="CASCADE"), index=True
    )
    user_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    joined_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    event: Mapped["Event"] = relationship("Event", back_populates="participants")
