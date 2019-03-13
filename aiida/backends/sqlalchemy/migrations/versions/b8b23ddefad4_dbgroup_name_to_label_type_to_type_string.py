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
"""DbGroup class: Rename name with label and type with type_string

Revision ID: b8b23ddefad4
Revises: 239cea6d2452
Create Date: 2018-12-06 15:25:32.865136

"""
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import
# pylint: disable=no-name-in-module,import-error
from alembic import op

# revision identifiers, used by Alembic.
revision = 'b8b23ddefad4'
down_revision = '239cea6d2452'
branch_labels = None
depends_on = None


def upgrade():
    """The upgrade migration actions."""
    # dropping
    op.drop_constraint('db_dbgroup_name_type_key', 'db_dbgroup')
    op.drop_index('ix_db_dbgroup_name', 'db_dbgroup')
    op.drop_index('ix_db_dbgroup_type', 'db_dbgroup')

    # renaming
    op.alter_column('db_dbgroup', 'name', new_column_name='label')
    op.alter_column('db_dbgroup', 'type', new_column_name='type_string')

    # creating
    op.create_unique_constraint('db_dbgroup_label_type_string_key', 'db_dbgroup', ['label', 'type_string'])
    op.create_index('ix_db_dbgroup_label', 'db_dbgroup', ['label'])
    op.create_index('ix_db_dbgroup_type_string', 'db_dbgroup', ['type_string'])


def downgrade():
    """The downgrade migration actions."""
    # dropping
    op.drop_constraint('db_dbgroup_label_type_string_key', 'db_dbgroup')
    op.drop_index('ix_db_dbgroup_label', 'db_dbgroup')
    op.drop_index('ix_db_dbgroup_type_string', 'db_dbgroup')

    # renaming
    op.alter_column('db_dbgroup', 'label', new_column_name='name')
    op.alter_column('db_dbgroup', 'type_string', new_column_name='type')

    # creating
    op.create_unique_constraint('db_dbgroup_name_type_key', 'db_dbgroup', ['name', 'type'])
    op.create_index('ix_db_dbgroup_name', 'db_dbgroup', ['name'])
    op.create_index('ix_db_dbgroup_type', 'db_dbgroup', ['type'])
