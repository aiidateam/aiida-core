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
"""Update all link labels with the value `_return`

This is the legacy default single link label.
The old process functions used to use `_return` as the default link label, however, since labels that start or end with
and underscore are illegal because they are used for namespacing.

This is identical to migration 118349c10896

Revision ID: django_0043
Revises: django_0042

"""
from alembic import op
import sqlalchemy as sa

revision = 'django_0043'
down_revision = 'django_0042'
branch_labels = None
depends_on = None


def upgrade():
    """Migrations for the upgrade."""
    conn = op.get_bind()
    statement = sa.text("""
        UPDATE db_dblink SET label='result' WHERE label = '_return';
    """)
    conn.execute(statement)


def downgrade():
    """Migrations for the downgrade."""
    statement = sa.text("""
        UPDATE db_dblink SET label='_result' WHERE label = 'return';
    """)
    op.get_bind().execute(statement)
