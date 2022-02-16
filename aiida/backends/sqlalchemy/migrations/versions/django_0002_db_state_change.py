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
"""Fix calculation states.

`UNDETERMINED` and `NOTFOUND` `dbcalcstate.state` values are replaced by `FAILED`.

Revision ID: django_0002
Revises: django_0001

"""
from alembic import op

revision = 'django_0002'
down_revision = 'django_0001'
branch_labels = None
depends_on = None


def upgrade():
    """Migrations for the upgrade."""
    # Note in the original django migration, a warning log was actually added to the node,
    # but we forgo that here
    op.execute("""
        UPDATE db_dbcalcstate
        SET state = 'FAILED'
        WHERE state = 'NOTFOUND'
    """)
    op.execute(
        """
        UPDATE db_dbcalcstate
        SET state = 'FAILED'
        WHERE state = 'UNDETERMINED'
    """
    )


def downgrade():
    """Migrations for the downgrade."""
    raise NotImplementedError('Downgrade of django_0002.')
