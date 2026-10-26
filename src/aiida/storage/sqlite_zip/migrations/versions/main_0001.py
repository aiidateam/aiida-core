###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Bring schema inline with profile database ``main_0002``.

Currently empty: the profile database ``main_0002`` invalidates stale
``CalcJobNode`` hashes, which does not apply to archives at the moment.
Kept as a placeholder to be filled in by future PRs.

Revision ID: main_0001
Revises: main_0000b

"""

revision = 'main_0001'
down_revision = 'main_0000b'
branch_labels = None
depends_on = None


def upgrade():
    """Migrations for the upgrade."""
    pass


def downgrade():
    """Migrations for the downgrade."""
    pass
