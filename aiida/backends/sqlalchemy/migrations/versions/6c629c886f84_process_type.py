# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Add the process_type column to DbNode

Revision ID: 6c629c886f84
Revises: 0aebbeab274d
Create Date: 2018-03-15 13:23:12.941148

"""
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '6c629c886f84'
down_revision = '0aebbeab274d'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('db_dbnode',
        sa.Column('process_type', sa.VARCHAR(length=255), autoincrement=False, nullable=True),
    )
    op.create_index('ix_db_dbnode_process_type', 'db_dbnode', ['process_type'])


def downgrade():
    op.drop_column('db_dbnode', 'process_type')
