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
"""Migration to add the `extras` JSONB column to the `DbGroup` model.

Revision ID: django_0045
Revises: django_0044

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = 'django_0045'
down_revision = 'django_0044'
branch_labels = None
depends_on = None


def upgrade():
    """Migrations for the upgrade."""
    # We add the column with a `server_default` because otherwise the migration would fail since existing rows will not
    # have a value and violate the not-nullable clause. However, the model doesn't use a server default but a default
    # on the ORM level, so we remove the server default from the column directly after.
    op.add_column(
        'db_dbgroup', sa.Column('extras', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='{}')
    )
    op.alter_column('db_dbgroup', 'extras', server_default=None)


def downgrade():
    """Migrations for the downgrade."""
    op.drop_column('db_dbgroup', 'extras')
