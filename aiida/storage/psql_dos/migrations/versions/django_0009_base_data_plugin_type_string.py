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
"""Change `db_dbnode.type` for base `Data` types.

The base Data types Bool, Float, Int and Str have been moved in the source code, which means that their
module path changes, which determines the plugin type string which is stored in the databse.
The type string now will have a type string prefix that is unique to each sub type.

Revision ID: django_0009
Revises: django_0008

"""
from alembic import op

revision = 'django_0009'
down_revision = 'django_0008'
branch_labels = None
depends_on = None


def upgrade():
    """Migrations for the upgrade."""
    op.execute(
        """
            UPDATE db_dbnode SET type = 'data.bool.Bool.' WHERE type = 'data.base.Bool.';
            UPDATE db_dbnode SET type = 'data.float.Float.' WHERE type = 'data.base.Float.';
            UPDATE db_dbnode SET type = 'data.int.Int.' WHERE type = 'data.base.Int.';
            UPDATE db_dbnode SET type = 'data.str.Str.' WHERE type = 'data.base.Str.';
            UPDATE db_dbnode SET type = 'data.list.List.' WHERE type = 'data.base.List.';
        """
    )


def downgrade():
    """Migrations for the downgrade."""
    op.execute(
        """
            UPDATE db_dbnode SET type = 'data.base.Bool.' WHERE type = 'data.bool.Bool.';
            UPDATE db_dbnode SET type = 'data.base.Float.' WHERE type = 'data.float.Float.';
            UPDATE db_dbnode SET type = 'data.base.Int.' WHERE type = 'data.int.Int.';
            UPDATE db_dbnode SET type = 'data.base.Str.' WHERE type = 'data.str.Str.';
            UPDATE db_dbnode SET type = 'data.base.List.' WHERE type = 'data.list.List.';
        """
    )
