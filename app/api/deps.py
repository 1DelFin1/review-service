from contextlib import asynccontextmanager
from typing import Annotated, AsyncGenerator

from fastapi import Depends
from faststream.rabbit import RabbitBroker

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.clients import BrokerMQ
from app.core.database import async_session_factory


async def get_session() -> AsyncGenerator:
    async with async_session_factory() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise


SessionDep = Annotated[AsyncSession, Depends(get_session)]
