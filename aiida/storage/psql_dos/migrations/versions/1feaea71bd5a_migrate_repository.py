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
"""Migrate the file repository to the new disk object store based implementation.

Revision ID: 1feaea71bd5a
Revises: 7536a82b2cc4
Create Date: 2020-10-01 15:05:49.271958

"""
from alembic import op

# revision identifiers, used by Alembic.
revision = '1feaea71bd5a'
down_revision = '7536a82b2cc4'
branch_labels = None
depends_on = None


def upgrade():
    """Migrations for the upgrade."""
    from aiida.storage.psql_dos.migrations.utils.migrate_repository import migrate_repository

    migrate_repository(op.get_bind(), op.get_context().opts['aiida_profile'])


def downgrade():
    """Migrations for the downgrade."""
    raise NotImplementedError('Migration of the file repository is not reversible.')
