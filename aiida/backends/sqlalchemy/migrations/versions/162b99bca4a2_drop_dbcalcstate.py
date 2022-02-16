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
"""Drop the DbCalcState table

Revision ID: 162b99bca4a2
Revises: a603da2cc809
Create Date: 2018-11-14 08:37:13.719646

"""
from alembic import op

# revision identifiers, used by Alembic.
revision = '162b99bca4a2'
down_revision = 'a603da2cc809'
branch_labels = None
depends_on = None


def upgrade():
    """Migrations for the upgrade."""
    op.drop_table('db_dbcalcstate')


def downgrade():
    """Migrations for the downgrade."""
    raise NotImplementedError('Downgrade of 162b99bca4a2.')
