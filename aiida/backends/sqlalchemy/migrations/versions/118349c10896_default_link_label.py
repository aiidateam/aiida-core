# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
# pylint: disable=invalid-name
"""Update all link labels with the value `_return`

This is the legacy default single link label.
The old process functions used to use `_return` as the default link label, however, since labels that start or end with
and underscore are illegal because they are used for namespacing.

This is identical to migration django_0043

Revision ID: 118349c10896
Revises: 91b573400be5
Create Date: 2019-11-21 09:43:45.006053

"""

# pylint: disable=no-member,no-name-in-module,import-error
from alembic import op
from sqlalchemy.sql import text

# revision identifiers, used by Alembic.
revision = '118349c10896'
down_revision = '91b573400be5'
branch_labels = None
depends_on = None


def upgrade():
    """Migrations for the upgrade."""
    conn = op.get_bind()

    # The old process functions used to use `_return` as the default link label, however, since labels that start or end
    # with and underscore are illegal.
    statement = text("""
        UPDATE db_dblink SET label='result' WHERE label = '_return';
    """)
    conn.execute(statement)


def downgrade():
    """Migrations for the downgrade."""
    raise NotImplementedError('Downgrade of 118349c10896.')
