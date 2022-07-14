# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
# pylint: disable=invalid-name,no-member
"""Move trajectory symbols from repository array to attribute

Note, this is similar to the sqlalchemy migration 12536798d4d3

Revision ID: django_0026
Revises: django_0025

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from aiida.storage.psql_dos.backend import get_filepath_container
from aiida.storage.psql_dos.migrations.utils.create_dbattribute import create_rows
from aiida.storage.psql_dos.migrations.utils.utils import load_numpy_array_from_repository

revision = 'django_0026'
down_revision = 'django_0025'
branch_labels = None
depends_on = None


def upgrade():
    """Migrations for the upgrade."""
    connection = op.get_bind()
    repo_path = get_filepath_container(op.get_context().opts['aiida_profile']).parent

    node_model = sa.table(
        'db_dbnode',
        sa.column('id', sa.Integer),
        sa.column('uuid', postgresql.UUID),
        sa.column('type', sa.String),
    )

    nodes = connection.execute(
        sa.select(node_model.c.id, node_model.c.uuid).where(
            node_model.c.type == op.inline_literal('node.data.array.trajectory.TrajectoryData.')
        )
    ).all()

    for node_id, uuid in nodes:
        value = load_numpy_array_from_repository(repo_path, uuid, 'symbols').tolist()
        for row in create_rows('symbols', value, node_id):
            connection.execute(sa.insert(sa.table('db_dbattribute', *(sa.column(key) for key in row))).values(**row))


def downgrade():
    """Migrations for the downgrade."""
    raise NotImplementedError('Downgrade of django_0026.')
