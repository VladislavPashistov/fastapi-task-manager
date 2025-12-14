from sqlalchemy import (
    DateTime, text, String, Text,
    ForeignKey, UniqueConstraint,
    Boolean, Index, false, func
)
from sqlalchemy.orm import relationship, mapped_column, Mapped
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from app.db import Base
from uuid import UUID
import datetime


class Task(Base):
    __tablename__ = "tasks"
    __table_args__ = (
        UniqueConstraint('user_id', 'title', name='unique_task_title'),
        Index('ix_tasks_user_completed', 'user_id', "is_completed"),
    )

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        server_default=text('gen_random_uuid()'),
        primary_key=True,
        nullable=False
    )
    title: Mapped[str] = mapped_column(
        String(100),
        nullable=False
    )
    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True
    )

    is_completed: Mapped[bool] = mapped_column(
        Boolean,
        server_default=false(),
        nullable=False
    )
    reminder_time: Mapped[datetime.datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )
    last_reminder_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        nullable=True
    )
    message_reminder: Mapped[str] = mapped_column(
        Text,
        nullable=True
    )
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    updated_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )

    # ForeignKey
    user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False
    )
    category_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("categories.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )

    # связи
    category: Mapped["Category"] = relationship(  # noqa: F821
        "Category",
        back_populates="tasks",
        passive_deletes=True
    )
    user: Mapped["User"] = relationship(  # noqa: F821
        'User',
        back_populates='tasks'
    )
