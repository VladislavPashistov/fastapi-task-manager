import datetime
from uuid import UUID
from typing import Annotated

from pydantic import BaseModel, Field, ConfigDict


class CreateTask(BaseModel):
    title: Annotated[str, Field(max_length=100)]
    description: str | None = None
    is_completed: bool = False
    reminder_time: datetime.datetime | None = None
    message_reminder: str | None = None
    category_id: UUID | None = None


class UpdateTask(BaseModel):
    title: Annotated[str | None, Field(max_length=100)] = None
    description: str | None = None
    is_completed: bool | None = None
    reminder_time: datetime.datetime | None = None
    message_reminder: str | None = None
    category_id: UUID | None = None


class ReadTask(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    title: str
    description: str | None
    is_completed: bool
    reminder_time: datetime.datetime | None = None
    message_reminder: str | None = None
    created_at: datetime.datetime
    updated_at: datetime.datetime
    user_id: UUID
    category_id: UUID | None
