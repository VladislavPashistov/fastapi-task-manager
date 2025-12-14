from enum import Enum

from sqlalchemy import DateTime, text, UniqueConstraint, Index, func, UUID as PG_UUID, Text

from sqlalchemy.orm import mapped_column, Mapped
from app.db import Base
from uuid import UUID
import datetime


class Channel(Enum):
    in_app = 'in_app'


class Status(Enum):
    pending = 'pending'
    sent = 'sent'
    failed = 'failed'


class Notification(Base):
    __tablename__ = 'notifications'
    __table_args__ = (
        UniqueConstraint('task_id', 'channel', name='uq_notifications_task_channel'),
        Index('ix_notifications_user_created_at', 'user_id', 'created_at'),
    )

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        index=True,
        server_default=text('gen_random_uuid()'),
        primary_key=True,
        nullable=False
    )

    user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        index=True,
        nullable=False,
    )
    task_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        index=True,
        nullable=False,
    )
    channel: Mapped[Channel] = mapped_column(
        nullable=False,
        server_default='in_app',
    )
    read_at: Mapped[datetime.datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    status: Mapped[Status] = mapped_column(
        server_default='pending',
        nullable=False,
    )
    message: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
