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
"""Unique constraints for the db_dbgroup_dbnodes table

Revision ID: 7a6587e16f4c
Revises: 35d4ee9a1b0e
Create Date: 2019-02-11 19:25:11.744902

"""
from alembic import op

# revision identifiers, used by Alembic.
revision = '7a6587e16f4c'
down_revision = '35d4ee9a1b0e'
branch_labels = None
depends_on = None


def upgrade():
    """
    Add unique constraints to the db_dbgroup_dbnodes table.
    """
    op.create_unique_constraint('uix_dbnode_id_dbgroup_id', 'db_dbgroup_dbnodes', ['dbnode_id', 'dbgroup_id'])


def downgrade():
    """
    Remove unique constraints from the db_dbgroup_dbnodes table.
    """
    op.drop_constraint('uix_dbnode_id_dbgroup_id', 'db_dbgroup_dbnodes')
