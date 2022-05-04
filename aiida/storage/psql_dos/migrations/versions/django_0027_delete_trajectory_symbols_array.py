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
"""Delete trajectory symbols array from the repository and the reference in the attributes.

Note, this is similar to the sqlalchemy migration ce56d84bcc35

Revision ID: django_0027
Revises: django_0026

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from sqlalchemy.sql.expression import delete

from aiida.storage.psql_dos.backend import get_filepath_container
from aiida.storage.psql_dos.migrations.utils import utils

revision = 'django_0027'
down_revision = 'django_0026'
branch_labels = None
depends_on = None


def upgrade():
    """Migrations for the upgrade."""
    # pylint: disable=unused-variable
    connection = op.get_bind()
    repo_path = get_filepath_container(op.get_context().opts['aiida_profile']).parent

    node_tbl = sa.table(
        'db_dbnode',
        sa.column('id', sa.Integer),
        sa.column('uuid', postgresql.UUID),
        sa.column('type', sa.String),
        # sa.column('attributes', JSONB),
    )

    nodes = connection.execute(
        sa.select(node_tbl.c.id, node_tbl.c.uuid).where(
            node_tbl.c.type == op.inline_literal('node.data.array.trajectory.TrajectoryData.')
        )
    ).all()

    attr_tbl = sa.table('db_dbattribute', sa.column('key'))

    for pk, uuid in nodes:
        connection.execute(delete(attr_tbl).where(sa.and_(node_tbl.c.id == pk, attr_tbl.c.key == 'array|symbols')))
        connection.execute(
            delete(attr_tbl).where(sa.and_(node_tbl.c.id == pk, attr_tbl.c.key.startswith('array|symbols.')))
        )
        utils.delete_numpy_array_from_repository(repo_path, uuid, 'symbols')


def downgrade():
    """Migrations for the downgrade."""
    raise NotImplementedError('Downgrade of django_0027.')
