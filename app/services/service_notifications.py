import datetime
from typing import List
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Channel, Notification


class NotificationNotFound(Exception):
    ...


# read_one_of_notification
async def read_one_of_ntf_service(
        db: AsyncSession,
        user_id: UUID,
        channel: Channel,
        ntf_id: UUID,
) -> Notification:
    res = (await db.execute(
        select(Notification)
        .where(
            Notification.user_id == user_id,
            Notification.channel == channel,
            Notification.id == ntf_id,
        ))).scalar_one_or_none()

    if res is None:
        raise NotificationNotFound()

    return res


# read_read_notification
async def read_read_ntf_service(
        db: AsyncSession,
        user_id: UUID,
        channel: Channel,
        limit, offset,
) -> List[Notification]:
    notis = (await db.execute(
        select(Notification)
        .where(
            Notification.user_id == user_id,
            Notification.channel == channel,
            Notification.read_at.is_not(None),
        )
        .order_by(Notification.read_at.desc(),
                  Notification.created_at.desc())
        .limit(limit)
        .offset(offset)
    )).scalars().all()

    result = list(notis)

    return result


# read_unread_notification
async def read_unread_ntf_service(
        limit: int,
        offset: int,
        db: AsyncSession,
        user_id: UUID,
        channel: Channel = Channel.in_app,
) -> List[Notification]:
    notis = (await db.execute(
        select(Notification)
        .where(
            Notification.user_id == user_id,
            Notification.channel == channel,
            Notification.read_at.is_(None),
        )
        .order_by(Notification.created_at.desc())
        .limit(limit)
        .offset(offset)
    )).scalars().all()

    return list(notis)


# mark_one_of_notification
async def mark_ntf_service(
        db: AsyncSession,
        user_id: UUID,
        ntf_id: UUID,
) -> None:
    noti = (await db.execute(
        select(Notification)
        .where(
            Notification.user_id == user_id,
            Notification.id == ntf_id,
            Notification.read_at.is_(None),
        )
    )).scalars().one_or_none()

    if noti is not None:
        noti.read_at = datetime.datetime.now(datetime.timezone.utc)

        await db.commit()
    else:
        raise NotificationNotFound()


# mark_all_notification
async def mark_all_ntf_service(
        db: AsyncSession,
        user_id: UUID,
        channel: Channel,
) -> None:
    now = datetime.datetime.now(datetime.timezone.utc)
    await db.execute(update(Notification)
                     .where(
        Notification.user_id == user_id,
        Notification.channel == channel,
        Notification.read_at.is_(None),
    ).values(read_at=now))
    await db.commit()
