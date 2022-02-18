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
"""Invalidating node hash.

Revision ID: django_0015
Revises: django_0014

"""
from alembic import op

revision = 'django_0015'
down_revision = 'django_0014'
branch_labels = None
depends_on = None

# Currently valid hash key
_HASH_EXTRA_KEY = '_aiida_hash'


def upgrade():
    """Migrations for the upgrade."""
    op.execute(f" DELETE FROM db_dbextra WHERE key='{_HASH_EXTRA_KEY}';")


def downgrade():
    """Migrations for the downgrade."""
    op.execute(f" DELETE FROM db_dbextra WHERE key='{_HASH_EXTRA_KEY}';")
