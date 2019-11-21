# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
# pylint: disable=invalid-name,too-few-public-methods
"""Update all link labels with the value `_return` which is the legacy default single link label.

The old process functions used to use `_return` as the default link label, however, since labels that start or end with
and underscore are illegal because they are used for namespacing.
"""

# Remove when https://github.com/PyCQA/pylint/issues/1931 is fixed
# pylint: disable=no-name-in-module,import-error
from django.db import migrations
from aiida.backends.djsite.db.migrations import upgrade_schema_version

REVISION = '1.0.43'
DOWN_REVISION = '1.0.42'


class Migration(migrations.Migration):
    """Migrate."""

    dependencies = [
        ('db', '0042_prepare_schema_reset'),
    ]

    operations = [
        migrations.RunSQL(
            sql=r"""
                UPDATE db_dblink SET label='result' WHERE label = '_return';
                """,
            reverse_sql=''
        ),
        upgrade_schema_version(REVISION, DOWN_REVISION)
    ]
