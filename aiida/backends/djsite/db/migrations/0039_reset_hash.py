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
"""
Invalidating node hash - User should rehash nodes for caching
"""

# Remove when https://github.com/PyCQA/pylint/issues/1931 is fixed
# pylint: disable=no-name-in-module,import-error
from django.db import migrations
from aiida.backends.djsite.db.migrations import upgrade_schema_version
from aiida.cmdline.utils import echo

REVISION = '1.0.39'
DOWN_REVISION = '1.0.38'

# Currently valid hash key
_HASH_EXTRA_KEY = '_aiida_hash'


def notify_user(apps, schema_editor):  # pylint: disable=unused-argument
    DbNode = apps.get_model('db', 'DbNode')
    if DbNode.objects.count():
        echo.echo_warning('Invalidating the hashes of all nodes. Please run "verdi rehash".', bold=True)


class Migration(migrations.Migration):
    """Invalidating node hash - User should rehash nodes for caching"""

    dependencies = [
        ('db', '0038_data_migration_legacy_job_calculations'),
    ]

    operations = [
        migrations.RunPython(notify_user, reverse_code=notify_user),
        migrations.RunSQL(
            f"UPDATE db_dbnode SET extras = extras #- '{{{_HASH_EXTRA_KEY}}}'::text[];",
            reverse_sql=f"UPDATE db_dbnode SET extras = extras #- '{{{_HASH_EXTRA_KEY}}}'::text[];"
        ),
        upgrade_schema_version(REVISION, DOWN_REVISION)
    ]
