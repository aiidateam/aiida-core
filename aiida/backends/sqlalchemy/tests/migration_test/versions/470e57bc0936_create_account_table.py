"""create account table

Revision ID: 470e57bc0936
Revises: 
Create Date: 2017-06-16 17:53:10.920345

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '470e57bc0936'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'account',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('name', sa.String(50), nullable=False),
        sa.Column('description', sa.Unicode(200)),
    )

def downgrade():
    op.drop_table('account')
