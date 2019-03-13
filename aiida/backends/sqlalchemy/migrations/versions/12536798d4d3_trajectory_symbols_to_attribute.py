# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Move trajectory symbols from repository array to attribute

Revision ID: 12536798d4d3
Revises: 37f3d4882837
Create Date: 2019-01-21 10:15:02.451308

"""
# pylint: disable=invalid-name
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
from __future__ import absolute_import

# Remove when https://github.com/PyCQA/pylint/issues/1931 is fixed
# pylint: disable=no-member,no-name-in-module,import-error

from alembic import op
from sqlalchemy import cast, String, Integer
from sqlalchemy.sql import table, column, select, func, text
from sqlalchemy.dialects.postgresql import UUID, JSONB

from aiida.backends.general.migrations.utils import load_numpy_array_from_repository

# revision identifiers, used by Alembic.
revision = '12536798d4d3'
down_revision = '37f3d4882837'
branch_labels = None
depends_on = None

# Here we duplicate the data stored in a TrajectoryData symbols array, storing it as an attribute.
# We delete the duplicates in the following migration (ce56d84bcc35) to avoid to delete data


def upgrade():
    """Migrations for the upgrade."""
    # yapf:disable
    connection = op.get_bind()

    DbNode = table('db_dbnode', column('id', Integer), column('uuid', UUID), column('type', String),
                   column('attributes', JSONB))

    nodes = connection.execute(
        select([DbNode.c.id, DbNode.c.uuid]).where(
            DbNode.c.type == op.inline_literal('node.data.array.trajectory.TrajectoryData.'))).fetchall()

    for pk, uuid in nodes:
        symbols = load_numpy_array_from_repository(uuid, 'symbols').tolist()
        connection.execute(DbNode.update().where(DbNode.c.id == pk).values(
            attributes=func.jsonb_set(DbNode.c.attributes, op.inline_literal('{"symbols"}'), cast(symbols, JSONB))))


def downgrade():
    """Migrations for the downgrade."""
    # yapf:disable
    connection = op.get_bind()

    DbNode = table('db_dbnode', column('id', Integer), column('uuid', UUID), column('type', String),
                   column('attributes', JSONB))

    nodes = connection.execute(
        select([DbNode.c.id, DbNode.c.uuid]).where(
            DbNode.c.type == op.inline_literal('node.data.array.trajectory.TrajectoryData.'))).fetchall()

    for pk, _ in nodes:
        connection.execute(
            text("""UPDATE db_dbnode SET attributes = attributes #- '{{symbols}}' WHERE id = {}""".format(pk)))
