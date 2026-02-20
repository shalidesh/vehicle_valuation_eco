"""initial schema

Revision ID: 001
Revises:
Create Date: 2025-12-09 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create users table
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('username', sa.String(length=100), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('password_hash', sa.String(length=255), nullable=False),
        sa.Column('role', sa.Enum('admin', 'manager', name='userrole'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)
    op.create_index(op.f('ix_users_id'), 'users', ['id'], unique=False)
    op.create_index(op.f('ix_users_username'), 'users', ['username'], unique=True)

    # Create fast_moving_vehicles table
    op.create_table(
        'fast_moving_vehicles',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('type', sa.String(length=20), nullable=False),
        sa.Column('manufacturer', sa.String(length=100), nullable=False),
        sa.Column('model', sa.String(length=100), nullable=False),
        sa.Column('yom', sa.Integer(), nullable=False),
        sa.Column('price', sa.DECIMAL(precision=15, scale=2), nullable=True),
        sa.Column('date', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_date', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_by', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['updated_by'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('type', 'manufacturer', 'model', 'yom', 'date', name='uix_fast_moving_vehicle_date')
    )
    op.create_index('idx_fast_moving_price_movement', 'fast_moving_vehicles', ['type', 'manufacturer', 'model', 'yom', 'date'], unique=False)
    op.create_index(op.f('ix_fast_moving_vehicles_date'), 'fast_moving_vehicles', ['date'], unique=False)
    op.create_index(op.f('ix_fast_moving_vehicles_id'), 'fast_moving_vehicles', ['id'], unique=False)
    op.create_index(op.f('ix_fast_moving_vehicles_manufacturer'), 'fast_moving_vehicles', ['manufacturer'], unique=False)
    op.create_index(op.f('ix_fast_moving_vehicles_model'), 'fast_moving_vehicles', ['model'], unique=False)
    op.create_index(op.f('ix_fast_moving_vehicles_type'), 'fast_moving_vehicles', ['type'], unique=False)

    # Create erp_model_mapping table
    op.create_table(
        'erp_model_mapping',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('manufacturer', sa.String(length=100), nullable=False),
        sa.Column('erp_name', sa.String(length=100), nullable=False),
        sa.Column('mapped_name', sa.String(length=100), nullable=False),
        sa.Column('updated_date', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_by', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['updated_by'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('manufacturer', 'erp_name', name='uix_erp_mapping')
    )
    op.create_index(op.f('ix_erp_model_mapping_erp_name'), 'erp_model_mapping', ['erp_name'], unique=False)
    op.create_index(op.f('ix_erp_model_mapping_id'), 'erp_model_mapping', ['id'], unique=False)
    op.create_index(op.f('ix_erp_model_mapping_manufacturer'), 'erp_model_mapping', ['manufacturer'], unique=False)

    # Create audit_log table
    op.create_table(
        'audit_log',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('table_name', sa.String(length=100), nullable=True),
        sa.Column('operation', sa.String(length=20), nullable=True),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('old_data', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('new_data', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('timestamp', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_audit_log_id'), 'audit_log', ['id'], unique=False)
    op.create_index(op.f('ix_audit_log_table_name'), 'audit_log', ['table_name'], unique=False)
    op.create_index(op.f('ix_audit_log_timestamp'), 'audit_log', ['timestamp'], unique=False)


def downgrade() -> None:
    # Drop tables in reverse order
    op.drop_index(op.f('ix_audit_log_timestamp'), table_name='audit_log')
    op.drop_index(op.f('ix_audit_log_table_name'), table_name='audit_log')
    op.drop_index(op.f('ix_audit_log_id'), table_name='audit_log')
    op.drop_table('audit_log')

    op.drop_index(op.f('ix_erp_model_mapping_manufacturer'), table_name='erp_model_mapping')
    op.drop_index(op.f('ix_erp_model_mapping_id'), table_name='erp_model_mapping')
    op.drop_index(op.f('ix_erp_model_mapping_erp_name'), table_name='erp_model_mapping')
    op.drop_table('erp_model_mapping')

    op.drop_index(op.f('ix_fast_moving_vehicles_type'), table_name='fast_moving_vehicles')
    op.drop_index(op.f('ix_fast_moving_vehicles_model'), table_name='fast_moving_vehicles')
    op.drop_index(op.f('ix_fast_moving_vehicles_manufacturer'), table_name='fast_moving_vehicles')
    op.drop_index(op.f('ix_fast_moving_vehicles_id'), table_name='fast_moving_vehicles')
    op.drop_index(op.f('ix_fast_moving_vehicles_date'), table_name='fast_moving_vehicles')
    op.drop_index('idx_fast_moving_price_movement', table_name='fast_moving_vehicles')
    op.drop_table('fast_moving_vehicles')

    op.drop_index(op.f('ix_users_username'), table_name='users')
    op.drop_index(op.f('ix_users_id'), table_name='users')
    op.drop_index(op.f('ix_users_email'), table_name='users')
    op.drop_table('users')

    # Drop enum type
    sa.Enum('admin', 'manager', name='userrole').drop(op.get_bind(), checkfirst=True)
