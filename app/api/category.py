from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.db import get_db
from app.schemas import CreateCategory, ReadCategory, UpdateCategory
from app.models import User
from app.services import (
    create_category_service,
    read_category_service,
    read_categories_service,
    update_category_service,
    delete_category_service
)

router_categories = APIRouter(prefix="/categories")


@router_categories.post("", response_model=ReadCategory, status_code=201)
async def create_category(
        data: CreateCategory,
        user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db),
):
    return await create_category_service(db=db, user=user, data=data)


@router_categories.get("", response_model=List[ReadCategory])
async def get_categories(
        user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db),
):
    return await read_categories_service(db=db, user=user)


@router_categories.get("/{category_id}", response_model=ReadCategory)
async def get_category(
        category_id: UUID,
        user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db),
):
    return await read_category_service(db=db, user=user, category_id=category_id)


@router_categories.delete("/{category_id}", status_code=204)
async def delete_category(
        category_id: UUID,
        user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db),
):
    await delete_category_service(db=db, user=user, category_id=category_id)


@router_categories.patch("/{category_id}", response_model=ReadCategory)
async def patch_category(
        category_id: UUID,
        data: UpdateCategory,
        user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db),
):
    return await update_category_service(db=db, user=user, category_id=category_id, data=data)
