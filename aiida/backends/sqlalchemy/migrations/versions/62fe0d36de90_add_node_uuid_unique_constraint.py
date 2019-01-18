# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Add a unique constraint on the UUID column of the Node model

Revision ID: 62fe0d36de90
Revises: 59edaf8a8b79
Create Date: 2018-07-02 17:50:42.929382

"""
from __future__ import division
from __future__ import absolute_import
from __future__ import print_function
from alembic import op

# revision identifiers, used by Alembic.
revision = '62fe0d36de90'
down_revision = '59edaf8a8b79'
branch_labels = None
depends_on = None


def verify_node_uuid_uniqueness():
    """Check whether the database contains nodes with duplicate UUIDS.

    Note that we have to redefine this method from aiida.manage.database.integrity.verify_node_uuid_uniqueness
    because that uses the default database connection, while here the one created by Alembic should be used instead.

    :raises: IntegrityError if database contains nodes with duplicate UUIDS.
    """
    from alembic import op
    from sqlalchemy.sql import text
    from aiida.common.exceptions import IntegrityError

    query = text(
        'SELECT s.id, s.uuid FROM (SELECT *, COUNT(*) OVER(PARTITION BY uuid) AS c FROM db_dbnode) AS s WHERE c > 1')
    conn = op.get_bind()
    duplicates = conn.execute(query).fetchall()

    if duplicates:
        table = 'db_dbnode'
        command = '`verdi database integrity detect-duplicate-uuid {table}`'.format(table)
        raise IntegrityError('Your table "{}" contains entries with duplicate UUIDS.\nRun {} '
                             'to return to a consistent state'.format(table, command))


def upgrade():
    verify_node_uuid_uniqueness()
    op.create_unique_constraint('db_dbnode_uuid_key', 'db_dbnode', ['uuid'])


def downgrade():
    op.drop_constraint('db_dbnode_uuid_key', 'db_dbnode')
