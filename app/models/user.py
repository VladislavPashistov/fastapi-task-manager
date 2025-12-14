from sqlalchemy import DateTime, text, String
from sqlalchemy.orm import relationship, mapped_column, Mapped

from app.db import Base
from uuid import UUID
import datetime


class User(Base):
    __tablename__ = 'users'

    id: Mapped[UUID] = mapped_column(
        server_default=text('gen_random_uuid()'),
        primary_key=True
    )
    username: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        nullable=False,
        index=True
    )
    email: Mapped[str] = mapped_column(
        String(254),  # стандарт RFC для email
        nullable=False,
        unique=True,
        index=True
    )
    hashed_password: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )
    fullname: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True
    )
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=text("TIMEZONE('utc', now())"),
        nullable=False,
        index=True
    )
    last_active_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=text("TIMEZONE('utc', now())"),
        nullable=False,
        index=True
    )

    # связи
    tasks: Mapped[list["Task"]] = relationship(  # noqa: F821
        "Task",
        back_populates="user",
        passive_deletes=True
    )
    categories: Mapped[list["Category"]] = relationship(  # noqa: F821
        "Category",
        back_populates="user",
        passive_deletes=True
    )
