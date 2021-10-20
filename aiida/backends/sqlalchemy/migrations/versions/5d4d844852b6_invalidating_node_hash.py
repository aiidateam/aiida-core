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
"""Invalidating node hash - User should rehash nodes for caching

Revision ID: 5d4d844852b6
Revises: 62fe0d36de90
Create Date: 2018-10-26 17:14:33.566670

"""
from alembic import op
# Remove when https://github.com/PyCQA/pylint/issues/1931 is fixed
# pylint: disable=no-name-in-module,import-error
from sqlalchemy.sql import text

# revision identifiers, used by Alembic.
revision = '5d4d844852b6'
down_revision = '62fe0d36de90'
branch_labels = None
depends_on = None

# Currently valid hash key
_HASH_EXTRA_KEY = '_aiida_hash'


def upgrade():
    """drop the hashes when upgrading"""
    conn = op.get_bind()  # pylint: disable=no-member

    # Invalidate all the hashes
    statement = text(f"UPDATE db_dbnode SET extras = extras #- '{{{_HASH_EXTRA_KEY}}}'::text[];")
    conn.execute(statement)


def downgrade():
    """drop the hashes also when downgrading"""
    conn = op.get_bind()  # pylint: disable=no-member

    # Invalidate all the hashes
    statement = text(f"UPDATE db_dbnode SET extras = extras #- '{{{_HASH_EXTRA_KEY}}}'::text[];")
    conn.execute(statement)
