from uuid import UUID, uuid4

from sqlalchemy import Integer, String, ForeignKey, Float
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.mixins import TimestampMixin


class ReviewModel(Base, TimestampMixin):
    __tablename__ = "reviews"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, nullable=False)
    user_id: Mapped[UUID] = mapped_column(default=uuid4, nullable=False)
    text: Mapped[str] = mapped_column(String(255), nullable=False)
    rating: Mapped[float] = mapped_column(Float, nullable=False)
    product_id: Mapped[int] = mapped_column(Integer, nullable=False)
