# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Correct the type string for the base data types

Revision ID: 0aebbeab274d
Revises: 7a6587e16f4c
Create Date: 2018-02-24 20:12:44.731358

"""
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import
from alembic import op
from sqlalchemy.sql import text


# revision identifiers, used by Alembic.
revision = '0aebbeab274d'
down_revision = '7a6587e16f4c'
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()

    # The base Data types Bool, Float, Int and Str have been moved in the source code, which means that their
    # module path changes, which determines the plugin type string which is stored in the databse.
    # The type string now will have a type string prefix that is unique to each sub type.
    statement = text("""
        UPDATE db_dbnode SET type = 'data.bool.Bool.' WHERE type = 'data.base.Bool.';
        UPDATE db_dbnode SET type = 'data.float.Float.' WHERE type = 'data.base.Float.';
        UPDATE db_dbnode SET type = 'data.int.Int.' WHERE type = 'data.base.Int.';
        UPDATE db_dbnode SET type = 'data.str.Str.' WHERE type = 'data.base.Str.';
        UPDATE db_dbnode SET type = 'data.list.List.' WHERE type = 'data.base.List.';
    """)
    conn.execute(statement)


def downgrade():
    conn = op.get_bind()

    statement = text("""
        UPDATE db_dbnode SET type = 'data.base.Bool.' WHERE type = 'data.bool.Bool.';
        UPDATE db_dbnode SET type = 'data.base.Float.' WHERE type = 'data.float.Float.';
        UPDATE db_dbnode SET type = 'data.base.Int.' WHERE type = 'data.int.Int.';
        UPDATE db_dbnode SET type = 'data.base.Str.' WHERE type = 'data.str.Str.';
        UPDATE db_dbnode SET type = 'data.base.List.' WHERE type = 'data.list.List.';
    """)
    conn.execute(statement)
