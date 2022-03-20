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
"""Change type of `code.Code.`.

Revision ID: django_0016
Revises: django_0015

"""
from alembic import op

revision = 'django_0016'
down_revision = 'django_0015'
branch_labels = None
depends_on = None


def upgrade():
    """Migrations for the upgrade."""
    op.execute("UPDATE db_dbnode SET type = 'data.code.Code.' WHERE type = 'code.Code.';")


def downgrade():
    """Migrations for the downgrade."""
    op.execute("UPDATE db_dbnode SET type = 'code.Code.' WHERE type = 'data.code.Code.';")
