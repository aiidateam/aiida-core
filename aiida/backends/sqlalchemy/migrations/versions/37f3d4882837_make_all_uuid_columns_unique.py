# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Make all uuid columns unique

Revision ID: 37f3d4882837
Revises: 6a5c2ea1439d
Create Date: 2018-11-17 17:18:58.691209

"""
# pylint: disable=invalid-name

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import
from alembic import op

# Remove when https://github.com/PyCQA/pylint/issues/1931 is fixed
# pylint: disable=no-member,no-name-in-module,import-error

# revision identifiers, used by Alembic.
revision = '37f3d4882837'
down_revision = '6a5c2ea1439d'
branch_labels = None
depends_on = None

tables = ['db_dbcomment', 'db_dbcomputer', 'db_dbgroup', 'db_dbworkflow']


def verify_uuid_uniqueness(table):
    """Check whether the database contains duplicate UUIDS.

    Note that we have to redefine this method from aiida.manage.database.integrity.verify_uuid_uniqueness
    because that uses the default database connection, while here the one created by Alembic should be used instead.

    :raises: IntegrityError if database contains nodes with duplicate UUIDS.
    """
    from sqlalchemy.sql import text
    from aiida.common.exceptions import IntegrityError

    query = text(
        'SELECT s.id, s.uuid FROM (SELECT *, COUNT(*) OVER(PARTITION BY uuid) AS c FROM {}) AS s WHERE c > 1'.format(
            table))
    conn = op.get_bind()
    duplicates = conn.execute(query).fetchall()

    if duplicates:
        command = '`verdi database integrity detect-duplicate-uuid {table}`'.format(table=table)
        raise IntegrityError('Your table "{}"" contains entries with duplicate UUIDS.\nRun {} '
                             'to return to a consistent state'.format(table, command))


def upgrade():

    for table in tables:
        verify_uuid_uniqueness(table)
        op.create_unique_constraint(table + '_uuid_key', table, ['uuid'])


def downgrade():

    for table in tables:
        op.drop_constraint(table + '_uuid_key', table)
