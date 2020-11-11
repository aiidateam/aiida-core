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
"""Invalidating node hash - User should rehash nodes for caching."""

# Remove when https://github.com/PyCQA/pylint/issues/1931 is fixed
# pylint: disable=no-name-in-module,import-error
from django.db import migrations
from aiida.backends.djsite.db.migrations import upgrade_schema_version

REVISION = '1.0.15'
DOWN_REVISION = '1.0.14'

# Currently valid hash key
_HASH_EXTRA_KEY = '_aiida_hash'


class Migration(migrations.Migration):
    """Invalidating node hash - User should rehash nodes for caching"""

    dependencies = [
        ('db', '0014_add_node_uuid_unique_constraint'),
    ]

    operations = [
        migrations.RunSQL(
            f" DELETE FROM db_dbextra WHERE key='{_HASH_EXTRA_KEY}';",
            reverse_sql=f" DELETE FROM db_dbextra WHERE key='{_HASH_EXTRA_KEY}';"
        ),
        upgrade_schema_version(REVISION, DOWN_REVISION)
    ]
