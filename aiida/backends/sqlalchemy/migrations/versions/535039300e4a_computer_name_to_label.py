# -*- coding: utf-8 -*-
# pylint: disable=invalid-name,no-member
"""Rename the ``name`` column of the ``Computer`` entity to ``label``.

Revision ID: 535039300e4a
Revises: 1feaea71bd5a
Create Date: 2021-04-28 14:11:40.728240

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '535039300e4a'
down_revision = '1feaea71bd5a'
branch_labels = None
depends_on = None


def upgrade():
    """Migrations for the upgrade."""
    op.add_column('db_dbcomputer', sa.Column('label', sa.String(length=255), nullable=False))
    op.drop_constraint('db_dbcomputer_name_key', 'db_dbcomputer', type_='unique')
    op.create_unique_constraint('db_dbcomputer_label_key', 'db_dbcomputer', ['label'])
    op.drop_column('db_dbcomputer', 'name')


def downgrade():
    """Migrations for the downgrade."""
    op.add_column('db_dbcomputer', sa.Column('name', sa.VARCHAR(length=255), autoincrement=False, nullable=False))
    op.drop_constraint('db_dbcomputer_label_key', 'db_dbcomputer', type_='unique')
    op.create_unique_constraint('db_dbcomputer_name_key', 'db_dbcomputer', ['name'])
    op.drop_column('db_dbcomputer', 'label')
