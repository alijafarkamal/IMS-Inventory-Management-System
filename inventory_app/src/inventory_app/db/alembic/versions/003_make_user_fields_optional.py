"""make user email and full_name optional

Revision ID: 003_user_optional_fields
Revises: 002_add_customers_activity
Create Date: 2025-12-04
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '003_user_optional_fields'
down_revision = '002_add_customers_activity'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Use batch operations for SQLite compatibility
    with op.batch_alter_table('users') as batch_op:
        batch_op.alter_column('email', existing_type=sa.String(length=100), nullable=True)
        batch_op.alter_column('full_name', existing_type=sa.String(length=100), nullable=True)


def downgrade() -> None:
    with op.batch_alter_table('users') as batch_op:
        batch_op.alter_column('email', existing_type=sa.String(length=100), nullable=False)
        batch_op.alter_column('full_name', existing_type=sa.String(length=100), nullable=False)
