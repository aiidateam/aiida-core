# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Data migration for after `ParameterData` was renamed to `Dict`.

Revision ID: d254fdfed416
Revises: 61fc0913fae9
Create Date: 2019-02-25 19:29:11.753089

"""
# pylint: disable=invalid-name,no-member,import-error,no-name-in-module
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import
from alembic import op
from sqlalchemy.sql import text

# revision identifiers, used by Alembic.
revision = 'd254fdfed416'
down_revision = '61fc0913fae9'
branch_labels = None
depends_on = None


def upgrade():
    """Migrations for the upgrade."""
    conn = op.get_bind()

    statement = text(r"""
        UPDATE db_dbnode SET type = 'data.dict.Dict.' WHERE type = 'data.parameter.ParameterData.';
    """)
    conn.execute(statement)


def downgrade():
    """Migrations for the downgrade."""
    conn = op.get_bind()

    statement = text(r"""
        UPDATE db_dbnode SET type = 'data.parameter.ParameterData.' WHERE type = 'data.dict.Dict.';
    """)
    conn.execute(statement)
