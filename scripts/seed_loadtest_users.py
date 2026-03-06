import asyncio
import os
from pathlib import Path
from typing import Iterable

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

from app.core.config import settings
from app.models.user import User
from app.core.security import hash_password


# создаём движок
async_engine = create_async_engine(
    settings.DATABASE_URL_ASYNC_,
    pool_pre_ping=True,
    echo=False
)


# создаём фабрику сессий
async_session = async_sessionmaker(
    bind=async_engine,
    expire_on_commit=False
)


def _iter_usernames(seed: int, n: int) -> Iterable[str]:
    for i in range(n):
        yield f"locust_{seed}_{i}"


async def main(
    *,
    n: int = 300,
    seed: int = 42,
    password: str = "12345678",
    batch_size: int = 100,
    out_file: str = "locust_users.txt",
) -> None:
    out_path = Path(out_file)
    tmp_path = out_path.with_suffix(out_path.suffix + ".tmp")

    # создаём недостающих в БД
    expected = list(_iter_usernames(seed, n))
    hashed = hash_password(password)

    async with async_session() as db:
        # забираем уже существующих из ожидаемого набора
        rows = await db.execute(select(User.username).where(User.username.in_(expected)))
        existing = set(rows.scalars().all())

        missing = [u for u in expected if u not in existing]

        if missing:
            batch = []
            for username in missing:
                email = f"{username}@example.com"

                batch.append(
                    User(
                        username=username,
                        email=email,
                        hashed_password=hashed,
                        fullname=None,
                    )
                )

                if len(batch) >= batch_size:
                    db.add_all(batch)
                    try:
                        await db.commit()
                    except IntegrityError:
                        await db.rollback()
                        raise
                    batch.clear()

            if batch:
                db.add_all(batch)
                try:
                    await db.commit()
                except IntegrityError:
                    await db.rollback()
                    raise

        # экспорт файла из БД (всегда пересобираем, чтобы не было рассинхрона)
        # берём только наш набор и в стабильном порядке.
        rows = await db.execute(
            select(User.username)
            .where(User.username.in_(expected))
            .order_by(User.username)
        )
        usernames = rows.scalars().all()

    # пишем атомарно: tmp -> replace
    tmp_path.parent.mkdir(parents=True, exist_ok=True)
    with open(tmp_path, "w", encoding="utf-8") as f:
        for u in usernames:
            f.write(f"{u}\n")

    os.replace(tmp_path, out_path)

    # быстрая проверка файла
    with open(out_path, "r", encoding="utf-8") as f:
        lines = sum(1 for _ in f)
    if lines != n:
        raise RuntimeError(f"Export mismatch: expected {n} lines, got {lines} in {out_path}")

if __name__ == "__main__":
    import time as t
    start = t.time()
    asyncio.run(main())
    print(t.time() - start)
