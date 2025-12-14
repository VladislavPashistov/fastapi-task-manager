from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from app.models import Status


class NotificationOut(BaseModel):
    id: UUID
    message: str
    status: Status
    created_at: datetime
    read_at: datetime | None = None
