# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
# pylint: disable=invalid-name,too-few-public-methods
"""Migration to reflect the name change of the built in calculation entry points in the database."""
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
from __future__ import absolute_import

# Remove when https://github.com/PyCQA/pylint/issues/1931 is fixed
# pylint: disable=no-name-in-module,import-error
from django.db import migrations

from aiida.backends.djsite.db.migrations import upgrade_schema_version

REVISION = '1.0.19'
DOWN_REVISION = '1.0.18'


class Migration(migrations.Migration):
    """Migration to remove entry point groups from process type strings and prefix unknown types with a marker."""

    dependencies = [
        ('db', '0018_django_1_11'),
    ]

    operations = [
        # The built in calculation plugins `arithmetic.add` and `templatereplacer` have been moved and their entry point
        # renamed. In the change the `simpleplugins` namespace was dropped so we migrate the existing nodes.
        migrations.RunSQL(
            sql="""
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
            """,
            reverse_sql="""
            UPDATE db_dbnode SET type = 'calculation.job.simpleplugins.arithmetic.add.ArithmeticAddCalculation.'
            WHERE type = 'calculation.job.arithmetic.add.ArithmeticAddCalculation.';

            UPDATE db_dbnode SET type = 'calculation.job.simpleplugins.templatereplacer.TemplatereplacerCalculation.'
            WHERE type = 'calculation.job.templatereplacer.TemplatereplacerCalculation.';

            UPDATE db_dbnode SET process_type = 'aiida.calculations:simpleplugins.arithmetic.add'
            WHERE process_type = 'aiida.calculations:arithmetic.add';

            UPDATE db_dbnode SET process_type = 'aiida.calculations:simpleplugins.templatereplacer'
            WHERE process_type = 'aiida.calculations:templatereplacer';

            UPDATE db_dbattribute AS a SET tval = 'simpleplugins.arithmetic.add'
            FROM db_dbnode AS n WHERE a.dbnode_id = n.id
                AND a.key = 'input_plugin'
                AND a.tval = 'arithmetic.add'
                AND n.type = 'data.code.Code.';

            UPDATE db_dbattribute AS a SET tval = 'simpleplugins.templatereplacer'
            FROM db_dbnode AS n WHERE a.dbnode_id = n.id
                AND a.key = 'input_plugin'
                AND a.tval = 'templatereplacer'
                AND n.type = 'data.code.Code.';
            """),
        upgrade_schema_version(REVISION, DOWN_REVISION)
    ]
