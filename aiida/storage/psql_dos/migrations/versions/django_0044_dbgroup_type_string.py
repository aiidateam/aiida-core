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

Revision ID: django_0044
Revises: django_0043

"""
from alembic import op
import sqlalchemy as sa

revision = 'django_0044'
down_revision = 'django_0043'
branch_labels = None
depends_on = None

forward_sql = [
    """UPDATE db_dbgroup SET type_string = 'core' WHERE type_string = 'user';""",
    """UPDATE db_dbgroup SET type_string = 'core.upf' WHERE type_string = 'data.upf';""",
    """UPDATE db_dbgroup SET type_string = 'core.import' WHERE type_string = 'auto.import';""",
    """UPDATE db_dbgroup SET type_string = 'core.auto' WHERE type_string = 'auto.run';""",
]


def upgrade():
    """Migrations for the upgrade."""
    conn = op.get_bind()
    statement = sa.text('\n'.join(forward_sql))
    conn.execute(statement)


def downgrade():
    """Migrations for the downgrade."""
    raise NotImplementedError('Downgrade of django_0044.')
