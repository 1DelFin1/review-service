from contextlib import asynccontextmanager
from typing import Annotated, AsyncGenerator

from fastapi import Depends
from faststream.rabbit import RabbitBroker

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.clients import BrokerMQ
from app.core.database import async_session_factory


async def get_session() -> AsyncSession:
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


@asynccontextmanager
async def get_broker() -> AsyncGenerator[RabbitBroker, None]:
    try:
        await BrokerMQ.connect()
        yield BrokerMQ
    finally:
        await BrokerMQ.close()


SessionDep = Annotated[AsyncSession, Depends(get_session)]
