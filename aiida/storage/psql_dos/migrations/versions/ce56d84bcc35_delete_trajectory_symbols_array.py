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
"""Delete trajectory symbols array from the repository and the reference in the attributes

Note, this is similar to the django migration django_0027

Revision ID: ce56d84bcc35
Revises: 12536798d4d3
Create Date: 2019-01-21 15:35:07.280805

"""
from alembic import op
from sqlalchemy import Integer, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.sql import column, select, table, text

from aiida.storage.psql_dos.backend import get_filepath_container
from aiida.storage.psql_dos.migrations.utils import utils

# revision identifiers, used by Alembic.
revision = 'ce56d84bcc35'
down_revision = '12536798d4d3'
branch_labels = None
depends_on = None


def upgrade():
    """Migrations for the upgrade."""
    connection = op.get_bind()
    repo_path = get_filepath_container(op.get_context().opts['aiida_profile']).parent

    DbNode = table(
        'db_dbnode',
        column('id', Integer),
        column('uuid', UUID),
        column('type', String),
        column('attributes', JSONB),
    )

    nodes = connection.execute(
        select(DbNode.c.id,
               DbNode.c.uuid).where(DbNode.c.type == op.inline_literal('node.data.array.trajectory.TrajectoryData.'))
    ).fetchall()

    for pk, uuid in nodes:
        connection.execute(
            text(f"""UPDATE db_dbnode SET attributes = attributes #- '{{array|symbols}}' WHERE id = {pk}""")
        )
        utils.delete_numpy_array_from_repository(repo_path, uuid, 'symbols')


def downgrade():
    """Migrations for the downgrade."""
    raise NotImplementedError('Downgrade of ce56d84bcc35.')
