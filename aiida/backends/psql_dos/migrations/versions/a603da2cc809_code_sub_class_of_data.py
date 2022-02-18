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
"""Correct the type string for the code class

Revision ID: a603da2cc809
Revises: 5d4d844852b6
Create Date: 2018-11-13 18:15:07.300709

"""
from alembic import op
from sqlalchemy.sql import text

# revision identifiers, used by Alembic.
revision = 'a603da2cc809'
down_revision = '5d4d844852b6'
branch_labels = None
depends_on = None


def upgrade():
    """Migrations for the upgrade."""
    conn = op.get_bind()

    # The Code class used to be just a sub class of Node but was changed to act like a Data node.
    # To make everything fully consistent, its type string should therefore also start with `data.`
    statement = text("""
        UPDATE db_dbnode SET type = 'data.code.Code.' WHERE type = 'code.Code.';
    """)
    conn.execute(statement)


def downgrade():
    """Migrations for the downgrade."""
    conn = op.get_bind()

    statement = text("""
        UPDATE db_dbnode SET type = 'code.Code.' WHERE type = 'data.code.Code.';
    """)
    conn.execute(statement)
