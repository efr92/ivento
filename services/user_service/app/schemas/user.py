from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class UserProfileCreateSchema(BaseModel):
    username: str = Field(min_length=3, max_length=100)
    avatar_url: Optional[str] = None
    bio: Optional[str] = None
    location: Optional[str] = None
    phone: Optional[str] = None


class UserProfileUpdateSchema(BaseModel):
    avatar_url: Optional[str] = None
    bio: Optional[str] = None
    location: Optional[str] = None
    phone: Optional[str] = None


class UserProfileResponseSchema(BaseModel):
    id: int
    user_id: int
    username: str
    avatar_url: Optional[str]
    bio: Optional[str]
    location: Optional[str]
    phone: Optional[str]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
