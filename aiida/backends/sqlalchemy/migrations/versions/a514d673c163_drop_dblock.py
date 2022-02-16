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
"""Drop the DbLock model

Revision ID: a514d673c163
Revises: f9a69de76a9a
Create Date: 2018-05-10 19:08:51.780194

"""
from alembic import op

# revision identifiers, used by Alembic.
revision = 'a514d673c163'
down_revision = 'f9a69de76a9a'
branch_labels = None
depends_on = None


def upgrade():
    """Migrations for the upgrade."""
    op.drop_table('db_dblock')


def downgrade():
    """Migrations for the downgrade."""
    raise NotImplementedError('Downgrade of a514d673c163.')
