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
"""Make all uuid columns unique

Revision ID: 37f3d4882837
Revises: 6a5c2ea1439d
Create Date: 2018-11-17 17:18:58.691209

"""
# pylint: disable=invalid-name

from alembic import op

# Remove when https://github.com/PyCQA/pylint/issues/1931 is fixed
# pylint: disable=no-member,no-name-in-module,import-error

# revision identifiers, used by Alembic.
revision = '37f3d4882837'
down_revision = '6a5c2ea1439d'
branch_labels = None
depends_on = None

tables = ['db_dbcomment', 'db_dbcomputer', 'db_dbgroup', 'db_dbworkflow']


def upgrade():
    """Migrations for the upgrade."""
    from aiida.storage.psql_dos.migrations.utils.duplicate_uuids import verify_uuid_uniqueness
    for table in tables:
        verify_uuid_uniqueness(table, op.get_bind())
        op.create_unique_constraint(f'{table}_uuid_key', table, ['uuid'])


def downgrade():
    """Migrations for the downgrade."""
    raise NotImplementedError('Downgrade of 37f3d4882837.')
