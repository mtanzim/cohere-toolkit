"""Add tool oauth table

Revision ID: bf8e28b5253b
Revises: a9b07acef4e8
Create Date: 2024-06-14 13:49:17.148119

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'bf8e28b5253b'
down_revision: Union[str, None] = 'a9b07acef4e8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    op.create_table(
        "tool_auth",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("user_id", sa.Text(), nullable=False),
        sa.Column("tool_id", sa.Text(), nullable=False),
        sa.Column("token_type", sa.Text(), nullable=False),
        sa.Column("encrypted_access_token", sa.LargeBinary(), nullable=True),
        sa.Column("encrypted_refresh_token", sa.LargeBinary(), nullable=True),
        sa.Column("expires_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("tool_auth_index", "tool_auth", ["user_id","tool_id"], unique=False)

def downgrade() -> None:
    op.drop_index("tool_auth_index", table_name="tool_auth")
    op.drop_table("tool_auth")
