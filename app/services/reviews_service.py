import asyncio

import aiohttp
from fastapi import HTTPException, status

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.clients import BrokerMQ
from app.core.config import settings
from app.exceptions import REVIEW_NOT_FOUND_EXCEPTION, REVIEW_ALREADY_EXISTS_EXCEPTION
from app.schemas import ReviewCreateSchema, ReviewUpdateSchema
from app.models.reviews import ReviewModel


class ReviewService:
    # TODO: переделать под httpx
    @staticmethod
    async def check_purchased_the_user(review_data: ReviewCreateSchema):
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{settings.urls.NGINX_URL}/orders/users/{review_data.user_id}/purchased-products/{review_data.product_id}"
                async with session.get(url, timeout=10) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data["has_purchased"]
                    elif response.status == 404:
                        return False
                    else:
                        raise HTTPException(
                            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail="Order service unavailable",
                        )
        except (aiohttp.ClientError, asyncio.TimeoutError):
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Cannot connect to order service",
            )

    @staticmethod
    async def get_avg_rating(session: AsyncSession, review_data: ReviewCreateSchema):
        stmt = (
            select(ReviewModel)
            .where(ReviewModel.product_id == review_data.product_id)
        )
        reviews = (await session.scalars(stmt)).all()
        sum_rating = 0
        for review in reviews:
            sum_rating += review.rating
        result = (sum_rating + review_data.rating) / (len(reviews) + 1)
        return round(result, 1)

    @classmethod
    async def create_review(
        cls,
        session: AsyncSession,
        review_data: ReviewCreateSchema
    ) -> dict:
        if not await cls.check_purchased_the_user(review_data):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User did not purchased this product",
            )

        stmt = (
            select(ReviewModel)
            .where(
                and_(
                    ReviewModel.product_id == review_data.product_id,
                    ReviewModel.user_id == review_data.user_id
                )
            )
        )
        review_existed = await session.scalar(stmt)

        if review_existed:
            raise REVIEW_ALREADY_EXISTS_EXCEPTION

        review = review_data.model_dump()
        new_review = ReviewModel(**review)
        session.add(new_review)

        await session.commit()

        new_rating = await cls.get_avg_rating(session, review_data)
        try:
            await BrokerMQ.publish({
                "new_rating": new_rating,
                "product_id": review_data.product_id
            }, queue="reviews")
        except Exception as e:
            print(e)

        return {"ok": True}

    @classmethod
    async def get_review_by_id(cls, session: AsyncSession, review_id: int) -> ReviewModel:
        stmt = (
            select(ReviewModel)
            .where(ReviewModel.id == review_id)
        )
        review = await session.scalar(stmt)
        if not review:
            raise REVIEW_NOT_FOUND_EXCEPTION
        return review

    @classmethod
    async def update_review(
        cls,
        session: AsyncSession,
        review_data: ReviewUpdateSchema,
        review_id: int
    ):
        review = await cls.get_review_by_id(session, review_id)
        new_review = review_data.model_dump(exclude_unset=True)
        for key, value in new_review.items():
            if new_review[key] != "":
                setattr(review, key, value)

        await session.commit()
        await session.refresh(review)
        return {"ok": True}

    @classmethod
    async def delete_review(cls, session: AsyncSession, review_id: int):
        review = await cls.get_review_by_id(session, review_id)
        await session.delete(review)
        await session.commit()
        return {"ok": True}
