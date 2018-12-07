"""DbGroup class: Rename name with label and type with type_string

Revision ID: b8b23ddefad4
Revises: 162b99bca4a2
Create Date: 2018-12-06 15:25:32.865136

"""
from __future__ import absolute_import
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'b8b23ddefad4'
down_revision = '162b99bca4a2'
branch_labels = None
depends_on = None


def upgrade():
    op.alter_column('db_dbgroup', 'name', new_column_name='label')
    op.alter_column('db_dbgroup', 'type', new_column_name='type_string')


def downgrade():
    op.alter_column('db_dbgroup', 'label', new_column_name='name')
    op.alter_column('db_dbgroup', 'type_string', new_column_name='type')
