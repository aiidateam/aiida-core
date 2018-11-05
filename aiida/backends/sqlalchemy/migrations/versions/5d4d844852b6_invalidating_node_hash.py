# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Invalidating node hash - User should rehash nodes for caching

Revision ID: 5d4d844852b6
Revises: 62fe0d36de90
Create Date: 2018-10-26 17:14:33.566670

"""
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import
from alembic import op
from sqlalchemy.sql import text
from aiida.cmdline.utils.echo import echo_warning

# revision identifiers, used by Alembic.
revision = '5d4d844852b6'
down_revision = '62fe0d36de90'
branch_labels = None
depends_on = None

# Currently valid hash key
_HASH_EXTRA_KEY = '_aiida_hash'

def upgrade():
    conn = op.get_bind()

    # Invalidate all the hashes & inform the user
    echo_warning("Invalidating all the hashes of all the nodes. Please run verdi rehash", bold=True)
    statement = text("""UPDATE db_dbnode SET extras = extras #- '{""" + _HASH_EXTRA_KEY + """}'::text[];""")
    conn.execute(statement)


def downgrade():
    conn = op.get_bind()

    # Invalidate all the hashes & inform the user
    echo_warning("Invalidating all the hashes of all the nodes. Please run verdi rehash", bold=True)
    statement = text("""UPDATE db_dbnode SET extras = extras #- '{""" + _HASH_EXTRA_KEY + """}'::text[];""")
    conn.execute(statement)
