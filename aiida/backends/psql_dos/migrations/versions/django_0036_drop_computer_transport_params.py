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
"""Drop `db_dbcomputer.transport_params`

This is similar to migration 07fac78e6209

Revision ID: django_0036
Revises: django_0035

"""
from alembic import op

revision = 'django_0036'
down_revision = 'django_0035'
branch_labels = None
depends_on = None


def upgrade():
    """Migrations for the upgrade."""
    op.drop_column('db_dbcomputer', 'transport_params')


def downgrade():
    """Migrations for the downgrade."""
    raise NotImplementedError('Downgrade of django_0036.')
