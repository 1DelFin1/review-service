from uuid import UUID

from pydantic import BaseModel, Field


class ReviewBaseSchema(BaseModel):
    user_id: UUID
    text: str = Field(max_length=255)
    product_id: int
    rating: float = Field(ge=1.0, le=5.0)


class ReviewCreateSchema(ReviewBaseSchema):
    pass


class ReviewUpdateSchema(BaseModel):
    user_id: UUID | None
    text: str | None = Field(max_length=255)
    product_id: int | None
    rating: float | None = Field(ge=1.0, le=5.0)
