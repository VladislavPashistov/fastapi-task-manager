import datetime
from uuid import UUID
from typing import Annotated

from pydantic import BaseModel, Field, ConfigDict, EmailStr


class LoginUser(BaseModel):
    login: Annotated[str, Field(min_length=4, max_length=254)]  # username или email
    password: Annotated[str, Field(min_length=8, max_length=255)]


class CreateUser(BaseModel):
    username: Annotated[str, Field(min_length=4, max_length=50)]
    password: Annotated[str, Field(min_length=8, max_length=255)]
    email: Annotated[EmailStr, Field(max_length=254)]
    fullname: Annotated[str | None, Field(max_length=100)] = None


class UpdateUser(BaseModel):
    username: Annotated[str | None, Field(min_length=4, max_length=50)] = None
    password: Annotated[str | None, Field(min_length=8, max_length=255)] = None
    email: Annotated[EmailStr | None, Field(max_length=254)] = None
    fullname: Annotated[str | None, Field(max_length=100)] = None


class ReadUser(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    username: str
    email: EmailStr
    fullname: str | None
    created_at: datetime.datetime
    last_active_at: datetime.datetime
