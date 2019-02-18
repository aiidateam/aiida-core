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
"""Final data migration for `Nodes` after `aiida.orm.nodes` reorganization was finalized to remove the `node.` prefix"""
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
from __future__ import absolute_import

# Remove when https://github.com/PyCQA/pylint/issues/1931 is fixed
# pylint: disable=no-name-in-module,import-error
from django.db import migrations
from aiida.backends.djsite.db.migrations import upgrade_schema_version

REVISION = '1.0.28'
DOWN_REVISION = '1.0.27'


class Migration(migrations.Migration):
    """Now all node sub classes live in `aiida.orm.nodes` so now the `node.` prefix can be removed."""

    dependencies = [
        ('db', '0027_delete_trajectory_symbols_array'),
    ]

    operations = [
        migrations.RunSQL(
            sql=r"""
                UPDATE db_dbnode
                SET type = regexp_replace(type, '^node.data.', 'data.')
                WHERE type LIKE 'node.data.%';

                UPDATE db_dbnode
                SET type = regexp_replace(type, '^node.process.', 'process.')
                WHERE type LIKE 'node.process.%';
                """,
            reverse_sql=r"""
                UPDATE db_dbnode
                SET type = regexp_replace(type, '^data.', 'node.data.')
                WHERE type LIKE 'data.%';

                UPDATE db_dbnode
                SET type = regexp_replace(type, '^process.', 'node.process.')
                WHERE type LIKE 'process.%';
                """),
        upgrade_schema_version(REVISION, DOWN_REVISION)
    ]
