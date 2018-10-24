# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Deleting dbpath table and triggers

Revision ID: 70c7d732f1b2
Revises:
Create Date: 2017-10-17 10:30:23.327195

"""
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from sqlalchemy.orm.session import Session
from aiida.backends.sqlalchemy.utils import install_tc

# revision identifiers, used by Alembic.
revision = '70c7d732f1b2'
down_revision = 'e15ef2630a1b'
branch_labels = None
depends_on = None


def upgrade():
    op.drop_table('db_dbpath')
    conn = op.get_bind()
    conn.execute("DROP TRIGGER IF EXISTS autoupdate_tc ON db_dblink")
    conn.execute("DROP FUNCTION IF EXISTS update_tc()")


def downgrade():
    op.create_table('db_dbpath',
    sa.Column('id', sa.INTEGER(), nullable=False),
    sa.Column('parent_id', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('child_id', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('depth', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('entry_edge_id', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('direct_edge_id', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('exit_edge_id', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.ForeignKeyConstraint(['child_id'], [u'db_dbnode.id'], name=u'db_dbpath_child_id_fkey', initially=u'DEFERRED', deferrable=True),
    sa.ForeignKeyConstraint(['parent_id'], [u'db_dbnode.id'], name=u'db_dbpath_parent_id_fkey', initially=u'DEFERRED', deferrable=True),
    sa.PrimaryKeyConstraint('id', name=u'db_dbpath_pkey')
    )
    # I get the session using the alembic connection
    # (Keep in mind that alembic uses the AiiDA SQLA
    # session)
    session = Session(bind=op.get_bind())
    install_tc(session)
