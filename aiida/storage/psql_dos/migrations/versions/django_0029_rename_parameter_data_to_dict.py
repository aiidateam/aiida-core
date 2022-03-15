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
"""Rename `db_dbnode.type` values `data.parameter.ParameterData.` to `data.dict.Dict.`

Note this is identical to migration d254fdfed416

Revision ID: django_0029
Revises: django_0028

"""
from alembic import op
import sqlalchemy as sa

revision = 'django_0029'
down_revision = 'django_0028'
branch_labels = None
depends_on = None


def upgrade():
    """Migrations for the upgrade."""
    conn = op.get_bind()

    statement = sa.text(
        r"""
        UPDATE db_dbnode SET type = 'data.dict.Dict.' WHERE type = 'data.parameter.ParameterData.';
    """
    )
    conn.execute(statement)


def downgrade():
    """Migrations for the downgrade."""
    raise NotImplementedError('Downgrade of django_0029.')
