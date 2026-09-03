###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Add archive support for contracted provenance.

Revision ID: main_0002
Revises: main_0001
Create Date: 2026-08-19

The database schema is unchanged. Bumping the archive format ensures readers
that do not understand contracted nodes and links reject these archives.
"""

revision = 'main_0002'
down_revision = 'main_0001'
branch_labels = None
depends_on = None


def upgrade():
    """Migrations for the upgrade."""


def downgrade():
    """Migrations for the downgrade."""
    raise NotImplementedError('Downgrade of main_0002.')
