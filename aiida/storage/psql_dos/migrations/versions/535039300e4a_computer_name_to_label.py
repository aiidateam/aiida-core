# -*- coding: utf-8 -*-
# pylint: disable=invalid-name,no-member
"""Rename `db_dbcomputer.name` to `db_dbcomputer.label`

Revision ID: 535039300e4a
Revises: 1feaea71bd5a
Create Date: 2021-04-28 14:11:40.728240

"""
from alembic import op

# revision identifiers, used by Alembic.
revision = '535039300e4a'
down_revision = '1feaea71bd5a'
branch_labels = None
depends_on = None


def upgrade():
    """Migrations for the upgrade."""
    op.drop_constraint('db_dbcomputer_name_key', 'db_dbcomputer')
    op.alter_column('db_dbcomputer', 'name', new_column_name='label')  # pylint: disable=no-member
    op.create_unique_constraint('db_dbcomputer_label_key', 'db_dbcomputer', ['label'])


def downgrade():
    """Migrations for the downgrade."""
    raise NotImplementedError('Downgrade of 535039300e4a.')
