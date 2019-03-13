# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Adding indexes and constraints to the dbnode-dbgroup relationship table

Revision ID: 59edaf8a8b79
Revises: a514d673c163
Create Date: 2018-06-22 14:50:18.447211

"""
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import
from alembic import op
from sqlalchemy.engine.reflection import Inspector

# revision identifiers, used by Alembic.
revision = '59edaf8a8b79'
down_revision = 'a514d673c163'
branch_labels = None
depends_on = None


def upgrade():
    # Check if constraint uix_dbnode_id_dbgroup_id of migration 7a6587e16f4c
    # is there and if yes, drop it
    insp = Inspector.from_engine(op.get_bind())
    for constr in insp.get_unique_constraints("db_dbgroup_dbnodes"):
        if constr['name'] == 'uix_dbnode_id_dbgroup_id':
            op.drop_constraint('uix_dbnode_id_dbgroup_id',
                               'db_dbgroup_dbnodes')

    op.create_index('db_dbgroup_dbnodes_dbnode_id_idx', 'db_dbgroup_dbnodes',
                    ['dbnode_id'])
    op.create_index('db_dbgroup_dbnodes_dbgroup_id_idx', 'db_dbgroup_dbnodes',
                    ['dbgroup_id'])
    op.create_unique_constraint(
        'db_dbgroup_dbnodes_dbgroup_id_dbnode_id_key', 'db_dbgroup_dbnodes',
        ['dbgroup_id', 'dbnode_id'])


def downgrade():
    op.drop_index('db_dbgroup_dbnodes_dbnode_id_idx', 'db_dbgroup_dbnodes')
    op.drop_index('db_dbgroup_dbnodes_dbgroup_id_idx', 'db_dbgroup_dbnodes')
    op.drop_constraint('db_dbgroup_dbnodes_dbgroup_id_dbnode_id_key',
                       'db_dbgroup_dbnodes')
    # Creating the constraint uix_dbnode_id_dbgroup_id that migration
    # 7a6587e16f4c would add
    op.create_unique_constraint(
        'db_dbgroup_dbnodes_dbgroup_id_dbnode_id_key', 'db_dbgroup_dbnodes',
        ['dbgroup_id', 'dbnode_id'])
