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
"""Deleting dbpath table and triggers

Revision ID: 70c7d732f1b2
Revises:
Create Date: 2017-10-17 10:30:23.327195

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '70c7d732f1b2'
down_revision = 'e15ef2630a1b'
branch_labels = None
depends_on = None


def upgrade():
    """Migrations for the upgrade."""
    op.drop_table('db_dbpath')
    conn = op.get_bind()
    conn.execute(sa.text('DROP TRIGGER IF EXISTS autoupdate_tc ON db_dblink'))
    conn.execute(sa.text('DROP FUNCTION IF EXISTS update_tc()'))


def downgrade():
    """Migrations for the downgrade."""
    raise NotImplementedError('Downgrade of 70c7d732f1b2.')
