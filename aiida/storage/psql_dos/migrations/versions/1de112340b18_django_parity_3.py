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
"""Parity with Django backend (rev: 0048),
part 3: Add PostgreSQL-specific indexes

Revision ID: 1de112340b18
Revises: 1de112340b17
Create Date: 2021-08-25 04:28:52.102767

"""
from alembic import op

from aiida.storage.psql_dos.migrations.utils.parity import synchronize_schemas

revision = '1de112340b18'
down_revision = '1de112340b17'
branch_labels = None
depends_on = None


def upgrade():
    """Migrations for the upgrade."""
    synchronize_schemas(op)


def downgrade():
    """Migrations for the downgrade."""
    raise NotImplementedError('Downgrade of 1de112340b18.')
