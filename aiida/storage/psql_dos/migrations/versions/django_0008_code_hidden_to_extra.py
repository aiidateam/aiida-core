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
"""Move `Code` `hidden` attribute from `db_dbextra` to `db_dbattribute`.

Revision ID: django_0008
Revises: django_0007

"""
from alembic import op

revision = 'django_0008'
down_revision = 'django_0007'
branch_labels = None
depends_on = None


def upgrade():
    """Migrations for the upgrade."""
    # The 'hidden' property of AbstractCode has been changed from an attribute to an extra
    # Therefore we find all nodes of type Code and if they have an attribute with the key 'hidden'
    # we move that value to the extra table
    #
    # First we copy the 'hidden' attributes from code.Code. nodes to the db_extra table
    op.execute(
        """
        INSERT INTO db_dbextra (key, datatype, tval, fval, ival, bval, dval, dbnode_id) (
            SELECT db_dbattribute.key, db_dbattribute.datatype, db_dbattribute.tval, db_dbattribute.fval,
            db_dbattribute.ival, db_dbattribute.bval, db_dbattribute.dval, db_dbattribute.dbnode_id
            FROM db_dbattribute JOIN db_dbnode ON db_dbnode.id = db_dbattribute.dbnode_id
            WHERE db_dbattribute.key = 'hidden'
                AND db_dbnode.type = 'code.Code.'
        );
    """
    )
    # Secondly, we delete the original entries from the DbAttribute table
    op.execute(
        """
        DELETE FROM db_dbattribute
        WHERE id in (
            SELECT db_dbattribute.id
            FROM db_dbattribute
            JOIN db_dbnode ON db_dbnode.id = db_dbattribute.dbnode_id
            WHERE db_dbattribute.key = 'hidden' AND db_dbnode.type = 'code.Code.'
        );
    """
    )


def downgrade():
    """Migrations for the downgrade."""
    raise NotImplementedError('Downgrade of django_0008.')
