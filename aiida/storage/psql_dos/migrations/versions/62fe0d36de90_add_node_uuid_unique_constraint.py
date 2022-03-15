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
"""Add a unique constraint on the UUID column of the Node model

Revision ID: 62fe0d36de90
Revises: 59edaf8a8b79
Create Date: 2018-07-02 17:50:42.929382

"""
from alembic import op

# revision identifiers, used by Alembic.
revision = '62fe0d36de90'
down_revision = '59edaf8a8b79'
branch_labels = None
depends_on = None


def upgrade():
    """Migrations for the upgrade."""
    from aiida.storage.psql_dos.migrations.utils.duplicate_uuids import verify_uuid_uniqueness
    verify_uuid_uniqueness('db_dbnode', op.get_bind())
    op.create_unique_constraint('db_dbnode_uuid_key', 'db_dbnode', ['uuid'])


def downgrade():
    """Migrations for the downgrade."""
    op.drop_constraint('db_dbnode_uuid_key', 'db_dbnode')
