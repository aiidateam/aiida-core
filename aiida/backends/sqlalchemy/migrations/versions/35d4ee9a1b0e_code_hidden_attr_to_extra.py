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
from alembic import op
from sqlalchemy.orm.session import Session
from sqlalchemy.orm.attributes import flag_modified
from aiida.backends.sqlalchemy.models.node import DbNode


# revision identifiers, used by Alembic.
revision = '35d4ee9a1b0e'
down_revision = '89176227b25'
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()
    session = Session(bind=conn)

    # The 'hidden' property of AbstractCode has been changed from an attribute to an extra
    # Therefore we find all nodes of type Code and if they have an attribute with the key 'hidden'
    # we move that value to the extra field
    codes = session.query(DbNode).filter(DbNode.type == 'code.Code.')
    for code in codes:
        if 'hidden' in code.attributes:
            session.add(code)

            hidden = code.attributes.pop('hidden')
            code.extras['hidden'] = hidden

            flag_modified(code, 'attributes')
            flag_modified(code, 'extras')

    session.flush()
    session.commit()


def downgrade():
    conn = op.get_bind()
    session = Session(bind=conn)

    # Reverse logic from the upgrade
    codes = session.query(DbNode).filter(DbNode.type == 'code.Code.')
    for code in codes:
        if 'hidden' in code.extras:
            session.add(code)

            hidden = code.extras.pop('hidden')
            code.attributes['hidden'] = hidden

            flag_modified(code, 'attributes')
            flag_modified(code, 'extras')

    session.flush()
    session.commit()