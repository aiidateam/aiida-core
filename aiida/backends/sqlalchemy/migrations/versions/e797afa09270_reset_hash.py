# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
# pylint: disable=invalid-name,too-few-public-methods,no-member
"""Invalidating node hash - User should rehash nodes for caching

Revision ID: e797afa09270
Revises: 26d561acd560
Create Date: 2019-07-01 19:39:33.605457

"""
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import
from alembic import op

# Remove when https://github.com/PyCQA/pylint/issues/1931 is fixed
# pylint: disable=no-name-in-module,import-error
from sqlalchemy.sql import text
from aiida.cmdline.utils.echo import echo_warning

# revision identifiers, used by Alembic.
revision = 'e797afa09270'
down_revision = '26d561acd560'
branch_labels = None
depends_on = None

# Currently valid hash key
_HASH_EXTRA_KEY = '_aiida_hash'


def upgrade():
    """drop the hashes when upgrading"""
    conn = op.get_bind()

    # Invalidate all the hashes & inform the user
    echo_warning("Invalidating all the hashes of all the nodes. Please run verdi rehash", bold=True)
    statement = text("""UPDATE db_dbnode SET extras = extras #- '{""" + _HASH_EXTRA_KEY + """}'::text[];""")
    conn.execute(statement)


def downgrade():
    """drop the hashes also when downgrading"""
    conn = op.get_bind()

    # Invalidate all the hashes & inform the user
    echo_warning("Invalidating all the hashes of all the nodes. Please run verdi rehash", bold=True)
    statement = text("""UPDATE db_dbnode SET extras = extras #- '{""" + _HASH_EXTRA_KEY + """}'::text[];""")
    conn.execute(statement)
