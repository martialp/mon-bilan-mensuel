"""fix_unique_transaction_constraint_for_null_statement_date

Revision ID: df7c67d9e31e
Revises: 9a3d3d48f010
Create Date: 2026-01-09

This migration fixes the unique constraint on transactions to properly handle
NULL statement_date values. PostgreSQL treats NULL values as distinct in unique
constraints, so we need to use partial unique indexes instead.
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'df7c67d9e31e'
down_revision = '9a3d3d48f010'
branch_labels = None
depends_on = None


def upgrade():
    # Drop the existing unique constraint that doesn't handle NULL properly
    op.drop_constraint('unique_transaction', 'transaction', type_='unique')
    
    # Create a partial unique index for transactions WITH statement_date
    op.create_index(
        'ix_unique_transaction_with_statement_date',
        'transaction',
        ['account_id', 'date_transaction', 'description', 'amount_cents', 'statement_date'],
        unique=True,
        postgresql_where=sa.text('statement_date IS NOT NULL')
    )
    
    # Create a partial unique index for transactions WITHOUT statement_date (NULL)
    op.create_index(
        'ix_unique_transaction_without_statement_date',
        'transaction',
        ['account_id', 'date_transaction', 'description', 'amount_cents'],
        unique=True,
        postgresql_where=sa.text('statement_date IS NULL')
    )


def downgrade():
    # Drop the partial indexes
    op.drop_index('ix_unique_transaction_without_statement_date', table_name='transaction')
    op.drop_index('ix_unique_transaction_with_statement_date', table_name='transaction')
    
    # Recreate the original unique constraint
    op.create_unique_constraint(
        'unique_transaction',
        'transaction',
        ['account_id', 'date_transaction', 'description', 'amount_cents', 'statement_date']
    )
