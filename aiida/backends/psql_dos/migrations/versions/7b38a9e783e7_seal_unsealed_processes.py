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
"""Seal any process nodes that have not yet been sealed but should.

This should have been accomplished by the last step in the previous migration, but because the WHERE clause was
incorrect, not all nodes that should have been targeted were included. The problem is with the statement:

    attributes->>'process_state' NOT IN ('created', 'running', 'waiting')

The problem here is that this will yield `False` if the attribute `process_state` does not even exist. This will be the
case for legacy calculations like `InlineCalculation` nodes. Their node type was already migrated in `0020` but most of
them will be unsealed.

This is identical to migration django_0041

Revision ID: 7b38a9e783e7
Revises: e734dd5e50d7
Create Date: 2019-10-28 13:22:56.224234

"""

# Remove when https://github.com/PyCQA/pylint/issues/1931 is fixed
# pylint: disable=no-name-in-module,import-error
from alembic import op
from sqlalchemy.sql import text

# revision identifiers, used by Alembic.
revision = '7b38a9e783e7'
down_revision = 'e734dd5e50d7'
branch_labels = None
depends_on = None


def upgrade():
    """Migrations for the upgrade."""
    conn = op.get_bind()

    statement = text(
        """
        UPDATE db_dbnode
        SET attributes = jsonb_set(attributes, '{"sealed"}', to_jsonb(True))
        WHERE
            node_type LIKE 'process.%' AND
            NOT attributes ? 'sealed' AND
            NOT (
                attributes ? 'process_state' AND
                attributes->>'process_state' IN ('created', 'running', 'waiting')
            );
        -- Set `sealed=True` for process nodes that do not yet have a `sealed` attribute AND are not in an active state
        -- It is important to check that `process_state` exists at all before doing the IN check.
        """
    )
    conn.execute(statement)


def downgrade():
    """Migrations for the downgrade."""
    raise NotImplementedError('Downgrade of 7b38a9e783e7.')
