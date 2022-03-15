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
"""Add a uniqueness constraint on `db_dbnode.uuid`.

Revision ID: django_0014
Revises: django_0013

"""
from alembic import op

revision = 'django_0014'
down_revision = 'django_0013'
branch_labels = None
depends_on = None


def upgrade():
    """Migrations for the upgrade."""
    from aiida.storage.psql_dos.migrations.utils.duplicate_uuids import verify_uuid_uniqueness
    verify_uuid_uniqueness('db_dbnode', op.get_bind())
    op.create_unique_constraint('db_dbnode_uuid_62e0bf98_uniq', 'db_dbnode', ['uuid'])
    op.drop_index('db_dbnode_uuid_62e0bf98', table_name='db_dbnode')


def downgrade():
    """Migrations for the downgrade."""
    raise NotImplementedError('Downgrade of django_0014.')
