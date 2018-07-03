"""Add a unique constraint on the UUID column of the Node model

Revision ID: 62fe0d36de90
Revises: 59edaf8a8b79
Create Date: 2018-07-02 17:50:42.929382

"""
from alembic import op


# revision identifiers, used by Alembic.
revision = '62fe0d36de90'
down_revision = '59edaf8a8b79'
branch_labels = None
depends_on = None


def upgrade():
    op.create_unique_constraint('db_dbnode_uuid_key', 'db_dbnode', ['uuid'])


def downgrade():
    op.drop_constraint('db_dbnode_uuid_key', 'db_dbnode')
