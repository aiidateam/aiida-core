# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
# pylint: disable=invalid-name
"""Migration to reflect the name change of the built in calculation entry points in the database.

Revision ID: 140c971ae0a3
Revises: 162b99bca4a2
Create Date: 2018-12-06 12:42:01.897037

"""
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import
from alembic import op

# Remove when https://github.com/PyCQA/pylint/issues/1931 is fixed
# pylint: disable=no-name-in-module,import-error
from sqlalchemy.sql import text

# revision identifiers, used by Alembic.
revision = '140c971ae0a3'
down_revision = '162b99bca4a2'
branch_labels = None
depends_on = None


def upgrade():
    """Migrations for the upgrade."""
    conn = op.get_bind()  # pylint: disable=no-member

    # The built in calculation plugins `arithmetic.add` and `templatereplacer` have been moved and their entry point
    # renamed. In the change the `simpleplugins` namespace was dropped so we migrate the existing nodes.
    statement = text("""
        UPDATE db_dbnode SET type = 'calculation.job.arithmetic.add.ArithmeticAddCalculation.'
        WHERE type = 'calculation.job.simpleplugins.arithmetic.add.ArithmeticAddCalculation.';

        UPDATE db_dbnode SET type = 'calculation.job.templatereplacer.TemplatereplacerCalculation.'
        WHERE type = 'calculation.job.simpleplugins.templatereplacer.TemplatereplacerCalculation.';

        UPDATE db_dbnode SET process_type = 'aiida.calculations:arithmetic.add'
        WHERE process_type = 'aiida.calculations:simpleplugins.arithmetic.add';

        UPDATE db_dbnode SET process_type = 'aiida.calculations:templatereplacer'
        WHERE process_type = 'aiida.calculations:simpleplugins.templatereplacer';

        UPDATE db_dbnode SET attributes = jsonb_set(attributes, '{"input_plugin"}', '"arithmetic.add"')
        WHERE attributes @> '{"input_plugin": "simpleplugins.arithmetic.add"}'
        AND type = 'data.code.Code.';

        UPDATE db_dbnode SET attributes = jsonb_set(attributes, '{"input_plugin"}', '"templatereplacer"')
        WHERE attributes @> '{"input_plugin": "simpleplugins.templatereplacer"}'
        AND type = 'data.code.Code.';
    """)
    conn.execute(statement)


def downgrade():
    """Migrations for the downgrade."""
    conn = op.get_bind()  # pylint: disable=no-member

    statement = text("""
        UPDATE db_dbnode SET type = 'calculation.job.simpleplugins.arithmetic.add.ArithmeticAddCalculation.'
        WHERE type = 'calculation.job.arithmetic.add.ArithmeticAddCalculation.';

        UPDATE db_dbnode SET type = 'calculation.job.simpleplugins.templatereplacer.TemplatereplacerCalculation.'
        WHERE type = 'calculation.job.templatereplacer.TemplatereplacerCalculation.';

        UPDATE db_dbnode SET process_type = 'aiida.calculations:simpleplugins.arithmetic.add'
        WHERE process_type = 'aiida.calculations:arithmetic.add';

        UPDATE db_dbnode SET process_type = 'aiida.calculations:simpleplugins.templatereplacer'
        WHERE process_type = 'aiida.calculations:templatereplacer';

        UPDATE db_dbnode SET attributes = jsonb_set(attributes, '{"input_plugin"}', '"simpleplugins.arithmetic.add"')
        WHERE attributes @> '{"input_plugin": "arithmetic.add"}'
        AND type = 'data.code.Code.';

        UPDATE db_dbnode SET attributes = jsonb_set(attributes, '{"input_plugin"}', '"simpleplugins.templatereplacer"')
        WHERE attributes @> '{"input_plugin": "templatereplacer"}'
        AND type = 'data.code.Code.';
    """)
    conn.execute(statement)
