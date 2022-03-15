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
"""Rename `db_dbgroup.type_string`.

Note this is identical to sqlalchemy migration e72ad251bcdb.

Revision ID: django_0022
Revises: django_0021

"""
from alembic import op

revision = 'django_0022'
down_revision = 'django_0021'
branch_labels = None
depends_on = None

forward_sql = [
    """UPDATE db_dbgroup SET type_string = 'user' WHERE type_string = '';""",
    """UPDATE db_dbgroup SET type_string = 'data.upf' WHERE type_string = 'data.upf.family';""",
    """UPDATE db_dbgroup SET type_string = 'auto.import' WHERE type_string = 'aiida.import';""",
    """UPDATE db_dbgroup SET type_string = 'auto.run' WHERE type_string = 'autogroup.run';""",
]


def upgrade():
    """Migrations for the upgrade."""
    op.execute('\n'.join(forward_sql))


def downgrade():
    """Migrations for the downgrade."""
    raise NotImplementedError('Downgrade of django_0022.')
