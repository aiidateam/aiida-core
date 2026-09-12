###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Bring schema inline with profile database ``main_0003``.

Currently empty: the profile database ``main_0003`` prepares the schema
for AiiDA v3.0.0, which does not apply to archives at the moment.
Kept as a placeholder to be filled in by future PRs.

Revision ID: main_0002
Revises: main_0001

"""

revision = 'main_0002'
down_revision = 'main_0001'
branch_labels = None
depends_on = None


def upgrade():
    """Migrations for the upgrade."""
    pass


def downgrade():
    """Migrations for the downgrade."""
    pass
