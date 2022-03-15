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
"""Add indexes to dbworkflowdata table

Revision ID: 89176227b25
Revises:
Create Date: 2017-11-03 11:06:00.327195

"""
from alembic import op

# revision identifiers, used by Alembic.
revision = '89176227b25'
down_revision = 'a6048f0ffca8'
branch_labels = None
depends_on = None


def upgrade():
    """Migrations for the upgrade."""
    op.create_index('ix_db_dbworkflowdata_aiida_obj_id', 'db_dbworkflowdata', ['aiida_obj_id'])
    op.create_index('ix_db_dbworkflowdata_parent_id', 'db_dbworkflowdata', ['parent_id'])


def downgrade():
    """Migrations for the downgrade."""
    raise NotImplementedError('Downgrade of 89176227b25.')
