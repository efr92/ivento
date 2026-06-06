from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class CommentCreateSchema(BaseModel):
    text: str = Field(min_length=1, max_length=2000)
    parent_id: Optional[int] = None


class CommentResponseSchema(BaseModel):
    id: int
    event_id: int
    user_id: int
    username: str
    text: str
    parent_id: Optional[int]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
