import asyncio
import logging
from datetime import datetime, timezone

import httpx
from fastapi import HTTPException, status

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.rabbit_config import rabbit_broker
from app.exceptions import REVIEW_NOT_FOUND_EXCEPTION, REVIEW_ALREADY_EXISTS_EXCEPTION
from app.schemas import ReviewCreateSchema, ReviewUpdateSchema
from app.models.reviews import ReviewModel


logger = logging.getLogger(__name__)


class ReviewService:
    @staticmethod
    async def _publish_review_event(
        event_type: str,
        product_ids: set[int] | list[int],
        review_id: int | None = None,
    ) -> None:
        normalized_product_ids = sorted(
            {
                int(product_id)
                for product_id in product_ids
                if isinstance(product_id, int) and product_id > 0
            }
        )

        if not normalized_product_ids:
            return

        payload: dict[str, object] = {
            "event_type": event_type,
            "product_ids": normalized_product_ids,
            "occurred_at": datetime.now(timezone.utc).isoformat(),
        }
        if review_id is not None:
            payload["review_id"] = review_id

        try:
            await rabbit_broker.publish(
                payload,
                routing_key=settings.rabbitmq.REVIEWS_ROUTING_KEY,
            )
        except Exception:
            logger.exception("Failed to publish review event: %s", payload)

    @staticmethod
    async def check_purchased_the_user(review_data: ReviewCreateSchema):
        try:
            async with httpx.AsyncClient() as client:
                url = (
                    f"{settings.urls.NGINX_URL}/orders/users/"
                    f"{review_data.user_id}/purchased-products/{review_data.product_id}"
                )
                response = await client.get(
                    url,
                    headers={"Content-Type": "application/json"},
                    timeout=10,
                )
                if response.status_code == 200:
                    data = response.json()
                    return data["has_purchased"]
                if response.status_code == 404:
                    return False
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Order service unavailable",
                )
        except (httpx.HTTPError, asyncio.TimeoutError):
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Cannot connect to order service",
            )

    @classmethod
    async def get_review_by_id(cls, session: AsyncSession, review_id: int) -> ReviewModel:
        stmt = select(ReviewModel).where(ReviewModel.id == review_id)
        review = await session.scalar(stmt)
        if not review:
            raise REVIEW_NOT_FOUND_EXCEPTION
        return review

    @classmethod
    async def update_review(
        cls,
        session: AsyncSession,
        review_data: ReviewUpdateSchema,
        review_id: int,
    ):
        review = await cls.get_review_by_id(session, review_id)
        previous_product_id = review.product_id

        new_review = review_data.model_dump(exclude_unset=True)
        for key, value in new_review.items():
            if value != "":
                setattr(review, key, value)

        await session.commit()
        await session.refresh(review)

        await cls._publish_review_event(
            event_type="review.updated",
            product_ids={previous_product_id, review.product_id},
            review_id=review.id,
        )
        return {"ok": True}

    @classmethod
    async def create_review(
        cls,
        session: AsyncSession,
        review_data: ReviewCreateSchema,
    ) -> dict:
        if not await cls.check_purchased_the_user(review_data):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User did not purchased this product",
            )

        stmt = select(ReviewModel).where(
            and_(
                ReviewModel.product_id == review_data.product_id,
                ReviewModel.user_id == review_data.user_id,
            )
        )
        review_existed = await session.scalar(stmt)

        if review_existed:
            raise REVIEW_ALREADY_EXISTS_EXCEPTION

        review = review_data.model_dump()
        new_review = ReviewModel(**review)
        session.add(new_review)

        await session.commit()
        await session.refresh(new_review)

        await cls._publish_review_event(
            event_type="review.created",
            product_ids={new_review.product_id},
            review_id=new_review.id,
        )
        return {"ok": True}

    @classmethod
    async def get_product_reviews(
        cls,
        session: AsyncSession,
        product_id: int,
    ) -> list[ReviewModel]:
        stmt = select(ReviewModel).where(ReviewModel.product_id == product_id)
        reviews = (await session.scalars(stmt)).all()
        return list(reviews)

    @classmethod
    async def delete_review(cls, session: AsyncSession, review_id: int):
        review = await cls.get_review_by_id(session, review_id)
        review_product_id = review.product_id
        review_entity_id = review.id

        await session.delete(review)
        await session.commit()

        await cls._publish_review_event(
            event_type="review.deleted",
            product_ids={review_product_id},
            review_id=review_entity_id,
        )
        return {"ok": True}
