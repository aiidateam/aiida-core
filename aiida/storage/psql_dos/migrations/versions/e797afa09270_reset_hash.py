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
"""Invalidating node hash

Users should rehash nodes for caching

Revision ID: e797afa09270
Revises: 26d561acd560
Create Date: 2019-07-01 19:39:33.605457

"""
from alembic import op

from aiida.storage.psql_dos.migrations.utils.integrity import drop_hashes

# revision identifiers, used by Alembic.
revision = 'e797afa09270'
down_revision = '26d561acd560'
branch_labels = None
depends_on = None


def upgrade():
    """drop the hashes when upgrading"""
    drop_hashes(op.get_bind())  # pylint: disable=no-member


def downgrade():
    """drop the hashes also when downgrading"""
    drop_hashes(op.get_bind())  # pylint: disable=no-member
