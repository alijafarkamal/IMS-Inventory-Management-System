"""add customers, activity_log, and supplier/customer columns on orders

Revision ID: 002_add_customers_activity
Revises: 001_initial
Create Date: 2025-11-28
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

# revision identifiers, used by Alembic.
revision = '002_add_customers_activity'
down_revision = '001_initial'
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()
    inspector = inspect(conn)

    # customers table
    if 'customers' not in inspector.get_table_names():
        op.create_table(
            'customers',
            sa.Column('id', sa.Integer(), primary_key=True, index=True),
            sa.Column('name', sa.String(length=100), nullable=False),
            sa.Column('email', sa.String(length=100)),
            sa.Column('phone', sa.String(length=20)),
            sa.Column('address', sa.Text()),
            sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.true()),
            sa.Column('created_at', sa.DateTime()),
            sa.Column('updated_at', sa.DateTime()),
        )

    # activity_log table
    if 'activity_log' not in inspector.get_table_names():
        op.create_table(
            'activity_log',
            sa.Column('id', sa.Integer(), primary_key=True, index=True),
            sa.Column('user_id', sa.Integer(), nullable=False),
            sa.Column('action', sa.String(length=100), nullable=False),
            sa.Column('entity_type', sa.String(length=50)),
            sa.Column('entity_id', sa.Integer()),
            sa.Column('details', sa.Text()),
            sa.Column('timestamp', sa.DateTime(), nullable=False),
            sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        )

    # add supplier_id and customer_id to orders using batch mode for SQLite
    with op.batch_alter_table('orders') as batch_op:
        batch_op.add_column(sa.Column('supplier_id', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('customer_id', sa.Integer(), nullable=True))


def downgrade() -> None:
    # drop FKs and columns from orders using batch mode
    with op.batch_alter_table('orders') as batch_op:
        # If constraints existed, SQLite would have handled them via recreate. We only drop columns.
        batch_op.drop_column('supplier_id')
        batch_op.drop_column('customer_id')

    # drop activity_log and customers
    op.drop_table('activity_log')
    op.drop_table('customers')
