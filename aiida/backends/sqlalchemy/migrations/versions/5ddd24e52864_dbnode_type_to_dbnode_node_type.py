# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
# pylint: disable=invalid-name,no-member
"""Renaming `DbNode.type` to `DbNode.node_type`

Revision ID: 5ddd24e52864
Revises: d254fdfed416
Create Date: 2019-02-22 17:09:57.715114

"""
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

# Remove when https://github.com/PyCQA/pylint/issues/1931 is fixed
# pylint: disable=no-name-in-module,import-error
from alembic import op

# revision identifiers, used by Alembic.
revision = '5ddd24e52864'
down_revision = 'd254fdfed416'
branch_labels = None
depends_on = None


def upgrade():
    """Migrations for the upgrade."""
    op.alter_column('db_dbnode', 'type', new_column_name='node_type')  # pylint: disable=no-member
    op.create_index(op.f('ix_db_dbnode_node_type'), 'db_dbnode', ['node_type'], unique=False)
    op.drop_index('ix_db_dbnode_type', table_name='db_dbnode')


def downgrade():
    """Migrations for the downgrade."""
    op.alter_column('db_dbnode', 'node_type', new_column_name='type')  # pylint: disable=no-member
    op.create_index('ix_db_dbnode_type', 'db_dbnode', ['type'], unique=False)
    op.drop_index(op.f('ix_db_dbnode_node_type'), table_name='db_dbnode')
