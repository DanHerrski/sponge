"""Add user_feedback column to nuggets table.

Revision ID: 0002_add_user_feedback
Revises: 0001_initial_p0_schema
Create Date: 2026-01-30
"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0002_add_user_feedback"
down_revision: Union[str, None] = "0001_initial_p0_schema"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create the user_feedback enum type
    user_feedback_enum = sa.Enum("up", "down", name="user_feedback")
    user_feedback_enum.create(op.get_bind(), checkfirst=True)

    # Add the user_feedback column to nuggets table
    op.add_column(
        "nuggets",
        sa.Column(
            "user_feedback",
            sa.Enum("up", "down", name="user_feedback"),
            nullable=True,
        ),
    )


def downgrade() -> None:
    # Remove the user_feedback column
    op.drop_column("nuggets", "user_feedback")

    # Drop the enum type
    user_feedback_enum = sa.Enum("up", "down", name="user_feedback")
    user_feedback_enum.drop(op.get_bind(), checkfirst=True)
