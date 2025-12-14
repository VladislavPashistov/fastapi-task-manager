from uuid import UUID
from typing import Annotated

from pydantic import BaseModel, Field, ConfigDict
from app.models.category import Color


class CreateCategory(BaseModel):
    name: Annotated[str, Field(max_length=50)]
    color: Color | None = None


class UpdateCategory(BaseModel):
    name: Annotated[str | None, Field(max_length=50)] = None
    color: Color | None = None


class ReadCategory(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    color: Color | None
    user_id: UUID
