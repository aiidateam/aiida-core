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
"""Change of the built in calculation entry points.

The built in calculation plugins `arithmetic.add` and `templatereplacer` have been moved and their entry point
renamed. In the change the `simpleplugins` namespace was dropped so we migrate the existing nodes.

Revision ID: django_0019
Revises: django_0018

"""
from alembic import op

revision = 'django_0019'
down_revision = 'django_0018'
branch_labels = None
depends_on = None


def upgrade():
    """Migrations for the upgrade."""
    op.execute(
        """
        UPDATE db_dbnode SET type = 'calculation.job.arithmetic.add.ArithmeticAddCalculation.'
        WHERE type = 'calculation.job.simpleplugins.arithmetic.add.ArithmeticAddCalculation.';

        UPDATE db_dbnode SET type = 'calculation.job.templatereplacer.TemplatereplacerCalculation.'
        WHERE type = 'calculation.job.simpleplugins.templatereplacer.TemplatereplacerCalculation.';

        UPDATE db_dbnode SET process_type = 'aiida.calculations:arithmetic.add'
        WHERE process_type = 'aiida.calculations:simpleplugins.arithmetic.add';

        UPDATE db_dbnode SET process_type = 'aiida.calculations:templatereplacer'
        WHERE process_type = 'aiida.calculations:simpleplugins.templatereplacer';

        UPDATE db_dbattribute AS a SET tval = 'arithmetic.add'
        FROM db_dbnode AS n WHERE a.dbnode_id = n.id
            AND a.key = 'input_plugin'
            AND a.tval = 'simpleplugins.arithmetic.add'
            AND n.type = 'data.code.Code.';

        UPDATE db_dbattribute AS a SET tval = 'templatereplacer'
        FROM db_dbnode AS n WHERE a.dbnode_id = n.id
            AND a.key = 'input_plugin'
            AND a.tval = 'simpleplugins.templatereplacer'
            AND n.type = 'data.code.Code.';
        """
    )


def downgrade():
    """Migrations for the downgrade."""
    raise NotImplementedError('Downgrade of django_0019.')
