###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Rename `db_dbnode.type` to `db_dbnode.node_type`

This is identical to migration django_0030

Revision ID: 5ddd24e52864
Revises: d254fdfed416
Create Date: 2019-02-22 17:09:57.715114

"""

from alembic import op

# revision identifiers, used by Alembic.
revision = '5ddd24e52864'
down_revision = 'd254fdfed416'
branch_labels = None
depends_on = None


def upgrade():
    """Migrations for the upgrade."""
    op.alter_column('db_dbnode', 'type', new_column_name='node_type')
    op.create_index(op.f('ix_db_dbnode_node_type'), 'db_dbnode', ['node_type'], unique=False)
    op.drop_index('ix_db_dbnode_type', table_name='db_dbnode')


def downgrade():
    """Migrations for the downgrade."""
    op.alter_column('db_dbnode', 'node_type', new_column_name='type')
    op.create_index('ix_db_dbnode_type', 'db_dbnode', ['type'], unique=False)
    op.drop_index(op.f('ix_db_dbnode_node_type'), table_name='db_dbnode')
