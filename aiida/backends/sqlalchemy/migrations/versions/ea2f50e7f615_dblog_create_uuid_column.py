# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
# pylint: disable=invalid-name,no-member
"""This migration creates UUID column and populates it with distinct UUIDs

This migration corresponds to the 0024_dblog_update Django migration.

Revision ID: ea2f50e7f615
Revises: 041a79fc615f
Create Date: 2019-01-30 19:22:50.984380

"""
# pylint: disable=no-name-in-module,import-error
from __future__ import division
from __future__ import absolute_import
from __future__ import print_function
from six.moves import zip
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'ea2f50e7f615'
down_revision = '041a79fc615f'
branch_labels = None
depends_on = None


def set_new_uuid(connection):
    """
    Set new and distinct UUIDs to all the logs
    """
    from aiida.common.utils import get_new_uuid

    # Exit if there are no rows - e.g. initial setup
    id_query = connection.execute('SELECT db_dblog.id FROM db_dblog')
    if id_query.rowcount == 0:
        return

    id_res = id_query.fetchall()
    ids = list()
    for (curr_id,) in id_res:
        ids.append(curr_id)
    uuids = set()
    while len(uuids) < len(ids):
        uuids.add(get_new_uuid())

    # Create the key/value pairs
    key_values = ",".join("({}, '{}')".format(curr_id, curr_uuid) for curr_id, curr_uuid in zip(ids, uuids))

    update_stm = """
        UPDATE db_dblog as t SET
            uuid = uuid(c.uuid)
        from (values {}) as c(id, uuid) where c.id = t.id""".format(key_values)
    connection.execute(update_stm)


def upgrade():
    """ Add an UUID column an populate it with unique UUIDs """
    from aiida.common.utils import get_new_uuid
    connection = op.get_bind()

    # Create the UUID column
    op.add_column('db_dblog',
                  sa.Column('uuid', postgresql.UUID(), autoincrement=False, nullable=True, default=get_new_uuid))

    # Populate the uuid column
    set_new_uuid(connection)


def downgrade():
    """ Remove the UUID column """
    op.drop_column('db_dblog', 'uuid')
