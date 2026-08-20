"""add_personal_goals_to_user_profiles

Revision ID: 3b4c5d6e7f8a
Revises: eff60b3a2e0e
Create Date: 2026-08-20 09:50:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '3b4c5d6e7f8a'
down_revision: Union[str, Sequence[str], None] = 'eff60b3a2e0e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Safely adds personal goal columns to user_profiles table preserving all existing user records."""
    op.add_column('user_profiles', sa.Column('goal_type', sa.String(length=50), nullable=True))
    op.add_column('user_profiles', sa.Column('goal_description', sa.String(length=255), nullable=True))
    op.add_column('user_profiles', sa.Column('goal_status', sa.String(length=20), server_default='ACTIVE', nullable=True))
    op.add_column('user_profiles', sa.Column('goal_created_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('user_profiles', sa.Column('goal_updated_at', sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    """Removes personal goal columns from user_profiles table."""
    op.drop_column('user_profiles', 'goal_updated_at')
    op.drop_column('user_profiles', 'goal_created_at')
    op.drop_column('user_profiles', 'goal_status')
    op.drop_column('user_profiles', 'goal_description')
    op.drop_column('user_profiles', 'goal_type')
