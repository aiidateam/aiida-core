# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
# pylint: disable=invalid-name
"""Data migration for `Data` nodes after it was moved in the `aiida.orm.node` module changing the type string."""

# Remove when https://github.com/PyCQA/pylint/issues/1931 is fixed
# pylint: disable=no-name-in-module,import-error
from django.db import migrations
from aiida.backends.djsite.db.migrations import upgrade_schema_version

REVISION = '1.0.25'
DOWN_REVISION = '1.0.24'


class Migration(migrations.Migration):
    """Data migration for `Data` nodes after it was moved in the `aiida.orm.node` module changing the type string."""

    dependencies = [
        ('db', '0024_dblog_update'),
    ]

    operations = [
        # The type string for `Data` nodes changed from `data.*` to `node.data.*`.
        migrations.RunSQL(
            sql=r"""
                UPDATE db_dbnode
                SET type = regexp_replace(type, '^data.', 'node.data.')
                WHERE type LIKE 'data.%'
                """,
            reverse_sql=r"""
                UPDATE db_dbnode
                SET type = regexp_replace(type, '^node.data.', 'data.')
                WHERE type LIKE 'node.data.%'
                """
        ),
        upgrade_schema_version(REVISION, DOWN_REVISION)
    ]
