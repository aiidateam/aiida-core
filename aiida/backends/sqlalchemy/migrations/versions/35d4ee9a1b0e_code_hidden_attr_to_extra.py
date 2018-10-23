# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Migrating 'hidden' properties from DbAttribute to DbExtra for code.Code. nodes

Revision ID: 35d4ee9a1b0e
Revises: 89176227b25
Create Date: 2018-02-21 22:00:43.460534

"""
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import
from alembic import op
from sqlalchemy.sql import text


# revision identifiers, used by Alembic.
revision = '35d4ee9a1b0e'
down_revision = '89176227b25'
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()

    # Set hidden=True in extras if the attributes contain hidden=True
    statement = text("""UPDATE db_dbnode SET extras = jsonb_set(extras, '{"hidden"}', to_jsonb(True)) WHERE type = 'code.Code.' AND attributes @> '{"hidden": true}'""")
    conn.execute(statement)

    # Set hidden=False in extras if the attributes contain hidden=False
    statement = text("""UPDATE db_dbnode SET extras = jsonb_set(extras, '{"hidden"}', to_jsonb(False)) WHERE type = 'code.Code.' AND attributes @> '{"hidden": false}'""")
    conn.execute(statement)

    # Delete the hidden key from the attributes
    statement = text("""UPDATE db_dbnode SET attributes = attributes-'hidden' WHERE type = 'code.Code.'""")
    conn.execute(statement)


def downgrade():
    conn = op.get_bind()

    # Set hidden=True in attributes if the extras contain hidden=True
    statement = text("""UPDATE db_dbnode SET attributes = jsonb_set(attributes, '{"hidden"}', to_jsonb(True)) WHERE type = 'code.Code.' AND extras @> '{"hidden": true}'""")
    conn.execute(statement)

    # Set hidden=False in attributes if the extras contain hidden=False
    statement = text("""UPDATE db_dbnode SET attributes = jsonb_set(attributes, '{"hidden"}', to_jsonb(False)) WHERE type = 'code.Code.' AND extras @> '{"hidden": false}'""")
    conn.execute(statement)

    # Delete the hidden key from the extras
    statement = text("""UPDATE db_dbnode SET extras = extras-'hidden' WHERE type = 'code.Code.'""")
    conn.execute(statement)
