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
"""Migration after the `Group` class became pluginnable and so the group `type_string` changed.

Revision ID: bf591f31dd12
Revises: 118349c10896
Create Date: 2020-03-31 10:00:52.609146

"""
# pylint: disable=no-name-in-module,import-error,invalid-name,no-member
from alembic import op
from sqlalchemy.sql import text

forward_sql = [
    """UPDATE db_dbgroup SET type_string = 'core' WHERE type_string = 'user';""",
    """UPDATE db_dbgroup SET type_string = 'core.upf' WHERE type_string = 'data.upf';""",
    """UPDATE db_dbgroup SET type_string = 'core.import' WHERE type_string = 'auto.import';""",
    """UPDATE db_dbgroup SET type_string = 'core.auto' WHERE type_string = 'auto.run';""",
]

# revision identifiers, used by Alembic.
revision = 'bf591f31dd12'
down_revision = '118349c10896'
branch_labels = None
depends_on = None


def upgrade():
    """Migrations for the upgrade."""
    conn = op.get_bind()
    statement = text('\n'.join(forward_sql))
    conn.execute(statement)


def downgrade():
    """Migrations for the downgrade."""
    raise NotImplementedError('Downgrade of bf591f31dd12.')
