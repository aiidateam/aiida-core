# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Data migration for `Data` nodes after it was moved in the `aiida.orm.node` module changing the type string.

Revision ID: 6a5c2ea1439d
Revises: 375c2db70663
Create Date: 2019-01-18 19:44:32.156083

"""
# pylint: disable=invalid-name,no-member,import-error,no-name-in-module
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import
from alembic import op
from sqlalchemy.sql import text

# revision identifiers, used by Alembic.
revision = '6a5c2ea1439d'
down_revision = '375c2db70663'
branch_labels = None
depends_on = None


def upgrade():
    """Migrations for the upgrade."""
    conn = op.get_bind()

    # The type string for `Data` nodes changed from `data.*` to `node.data.*`.
    statement = text(r"""
        UPDATE db_dbnode
        SET type = regexp_replace(type, '^data.', 'node.data.')
        WHERE type LIKE 'data.%'
    """)
    conn.execute(statement)


def downgrade():
    """Migrations for the downgrade."""
    conn = op.get_bind()

    statement = text(r"""
        UPDATE db_dbnode
        SET type = regexp_replace(type, '^node.data.', 'data.')
        WHERE type LIKE 'node.data.%'
    """)
    conn.execute(statement)
