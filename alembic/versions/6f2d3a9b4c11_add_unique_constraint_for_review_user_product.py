"""add unique constraint for review user/product

Revision ID: 6f2d3a9b4c11
Revises: e125e037ef11
Create Date: 2026-03-25 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "6f2d3a9b4c11"
down_revision: Union[str, Sequence[str], None] = "e125e037ef11"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_unique_constraint(
        "uq_reviews_user_id_product_id",
        "reviews",
        ["user_id", "product_id"],
    )


def downgrade() -> None:
    op.drop_constraint(
        "uq_reviews_user_id_product_id",
        "reviews",
        type_="unique",
    )
