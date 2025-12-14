from sqlalchemy import text, String, ForeignKey, UniqueConstraint, Enum as SQLEnum
from sqlalchemy.orm import relationship, mapped_column, Mapped

from enum import StrEnum
from app.db import Base
from uuid import UUID


class Color(StrEnum):
    blue = 'blue'
    red = 'red'
    green = 'green'
    yellow = 'yellow'
    magenta = 'magenta'
    cyan = 'cyan'
    white = 'white'
    black = 'black'
    pink = 'pink'
    gray = 'gray'
    orange = 'orange'
    purple = 'purple'


class Category(Base):
    __tablename__ = 'categories'
    __table_args__ = (
        UniqueConstraint("user_id", "name", name="unique_category_name"),
    )

    id: Mapped[UUID] = mapped_column(
        server_default=text('gen_random_uuid()'),
        primary_key=True,
        nullable=False
    )

    name: Mapped[str] = mapped_column(
        String(50),
        nullable=False
    )
    color: Mapped[Color | None] = mapped_column(
        SQLEnum(Color),
        nullable=True
    )

    # ForeignKey
    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    # связи
    user: Mapped["User"] = relationship(  # noqa: F821
        "User",
        back_populates="categories",
        passive_deletes=True
    )
    tasks: Mapped[list["Task"]] = relationship(  # noqa: F821
        "Task",
        back_populates="category",
        passive_deletes=True
    )
