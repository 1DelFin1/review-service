from aiormq.tools import awaitable
from fastapi import APIRouter, Depends

from app.api.deps import SessionDep
from app.models import ReviewModel
from app.services import ReviewService
from app.schemas import ReviewCreateSchema, ReviewUpdateSchema


reviews_router = APIRouter(prefix="/reviews", tags=["reviews"])


@reviews_router.post("")
async def create_review(
    session: SessionDep,
    review_data: ReviewCreateSchema,
):
    review = await ReviewService.create_review(session, review_data)
    return review


@reviews_router.get("/{review_id}")
async def get_review_by_id(session: SessionDep, review_id: int):
    review = await ReviewService.get_review_by_id(session, review_id)
    return review


@reviews_router.patch("/{review_id}")
async def update_review(
    session: SessionDep, user_data: ReviewUpdateSchema, review_id: int
):
    review = await ReviewService.update_review(session, user_data, review_id)
    return review


@reviews_router.delete("/{review_id}")
async def delete_review(session: SessionDep, review_id: int):
    review = await ReviewService.delete_review(session, review_id)
    return review


@reviews_router.get("/product/{product_id}")
async def get_product_reviews(
    session: SessionDep,
    product_id: int,
):
    return await ReviewService.get_product_reviews(session, product_id)
