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
""""Invalidating node hashes

Users should rehash nodes for caching

Revision ID: django_0039
Revises: django_0038

"""
from alembic import op

from aiida.storage.psql_dos.migrations.utils.integrity import drop_hashes

revision = 'django_0039'
down_revision = 'django_0038'
branch_labels = None
depends_on = None


def upgrade():
    """Migrations for the upgrade."""
    drop_hashes(op.get_bind())  # pylint: disable=no-member


def downgrade():
    """Migrations for the downgrade."""
    drop_hashes(op.get_bind())  # pylint: disable=no-member
