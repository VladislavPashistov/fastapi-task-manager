from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.db import get_db
from app.schemas import CreateTask, ReadTask, UpdateTask
from app.models import User
from app.services import (
    create_task_service, read_task_service, read_tasks_service,
    update_task_service, delete_task_service
)

router_task = APIRouter(prefix="/tasks")


@router_task.post("", response_model=ReadTask, status_code=201)
async def create_task(data: CreateTask,
                      db: AsyncSession = Depends(get_db),
                      current_user: User = Depends(get_current_user)):
    return await create_task_service(data=data, db=db, user=current_user)


@router_task.get("/{task_id}", response_model=ReadTask)
async def get_task(task_id: UUID,
                   db: AsyncSession = Depends(get_db),
                   current_user: User = Depends(get_current_user)):
    return await read_task_service(task_id=task_id, db=db, user=current_user)


@router_task.get("", response_model=List[ReadTask])
async def get_tasks(db: AsyncSession = Depends(get_db),
                    current_user: User = Depends(get_current_user),
                    page: int = Query(1, ge=1),
                    per_page: int = Query(20, ge=1, le=100)):
    return await read_tasks_service(db=db, page=page, per_page=per_page, user=current_user)


@router_task.delete("/{task_id}", status_code=204)
async def delete_task(task_id: UUID,
                      db: AsyncSession = Depends(get_db),
                      current_user: User = Depends(get_current_user)):
    await delete_task_service(task_id=task_id, db=db, user_id=current_user.id)


@router_task.patch("/{task_id}", response_model=ReadTask)
async def patch_task(task_id: UUID,
                     data: UpdateTask,
                     db: AsyncSession = Depends(get_db),
                     current_user: User = Depends(get_current_user)):
    return await update_task_service(task_id=task_id, data=data, db=db, user=current_user)
