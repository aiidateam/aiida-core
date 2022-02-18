# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
# pylint: disable=invalid-name,no-member,no-name-in-module,import-error
"""This migration creates UUID column and populates it with distinct UUIDs

This migration corresponds to the 0024_dblog_update Django migration (only the final part).

Revision ID: ea2f50e7f615
Revises: 041a79fc615f
Create Date: 2019-01-30 19:22:50.984380
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'ea2f50e7f615'
down_revision = '041a79fc615f'
branch_labels = None
depends_on = None


def upgrade():
    """ Add an UUID column an populate it with unique UUIDs """
    from aiida.common.utils import get_new_uuid
    from aiida.storage.psql_dos.migrations.utils.dblog_update import set_new_uuid

    connection = op.get_bind()

    # Create the UUID column
    op.add_column(
        'db_dblog', sa.Column('uuid', postgresql.UUID(), autoincrement=False, nullable=True, default=get_new_uuid)
    )

    # Populate the uuid column
    set_new_uuid(connection)


def downgrade():
    """ Remove the UUID column """
    op.drop_column('db_dblog', 'uuid')
