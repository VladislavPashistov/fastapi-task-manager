from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from app.api.deps import get_current_user
from app.db import get_db
from app.schemas import NotificationOut
from app.models import User, Channel
from app.services import (
    read_one_of_ntf_service, read_read_ntf_service, read_unread_ntf_service,
    mark_ntf_service, mark_all_ntf_service,
)

router_notifications = APIRouter(prefix='/notifications')


# читать все прочитанные
@router_notifications.get('/read', response_model=List[NotificationOut])
async def read_read_notification(
        db: AsyncSession = Depends(get_db),
        limit: int = Query(20, ge=1, le=100),
        offset: int = Query(0, ge=0),
        user: User = Depends(get_current_user),
        channel: Channel = Channel.in_app):
    return await read_read_ntf_service(
        db=db,
        user_id=user.id,
        channel=channel,
        limit=limit,
        offset=offset,
    )


# читать все непрочитанные
@router_notifications.get('/unread', response_model=List[NotificationOut])
async def read_unread_notification(
        db: AsyncSession = Depends(get_db),
        user: User = Depends(get_current_user),
        limit: int = Query(20, ge=1, le=100),
        offset: int = Query(0, ge=0),
):
    channel = Channel.in_app
    return await read_unread_ntf_service(db=db,
                                         user_id=user.id,
                                         channel=channel,
                                         limit=limit,
                                         offset=offset
                                         )


# читать один
@router_notifications.get('/{ntf_id}', response_model=NotificationOut)
async def read_one_of_notification(
        ntf_id: UUID,
        db: AsyncSession = Depends(get_db),
        user: User = Depends(get_current_user),
        channel: Channel = Channel.in_app):
    return await read_one_of_ntf_service(db=db,
                                         user_id=user.id,
                                         channel=channel,
                                         ntf_id=ntf_id
                                         )


# пометить один
@router_notifications.post("/{ntf_id}/read", status_code=status.HTTP_204_NO_CONTENT)
async def mark_one_of_notification(
        ntf_id: UUID,
        db: AsyncSession = Depends(get_db),
        user: User = Depends(get_current_user),
):
    await mark_ntf_service(db=db,
                           user_id=user.id,
                           ntf_id=ntf_id,
                           )


# пометить все
@router_notifications.post("/read-all", status_code=status.HTTP_204_NO_CONTENT)
async def mark_all_notification(
        db: AsyncSession = Depends(get_db),
        user: User = Depends(get_current_user),
        channel: Channel = Channel.in_app
):
    await mark_all_ntf_service(db=db,
                               user_id=user.id,
                               channel=channel,
                               )
