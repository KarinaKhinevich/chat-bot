"""Add summary column to documents table

Revision ID: 001_add_summary_column
Revises: 
Create Date: 2025-09-17

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '001_add_summary_column'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Add summary column to documents table
    op.add_column('documents', sa.Column('summary', sa.Text(), nullable=True))
    
    # Update existing records to have empty summary
    op.execute("UPDATE documents SET summary = '' WHERE summary IS NULL")
    
    # Make the column non-nullable after updating existing records
    op.alter_column('documents', 'summary', nullable=False)


def downgrade():
    # Remove summary column
    op.drop_column('documents', 'summary')