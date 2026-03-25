from contextlib import asynccontextmanager

import uvicorn

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.clients import BrokerMQ
from app.api.routers import reviews_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    await BrokerMQ.start()
    yield
    await BrokerMQ.close()


app = FastAPI(title="review-service", lifespan=lifespan)
app.include_router(reviews_router)


app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=settings.cors.CORS_METHODS,
    allow_headers=settings.cors.CORS_HEADERS,
)


if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8001, reload=True)
