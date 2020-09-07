# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Migration to add the `extras` JSONB column to the `DbGroup` model."""
# pylint: disable=invalid-name
import django.contrib.postgres.fields.jsonb
from django.db import migrations
from aiida.backends.djsite.db.migrations import upgrade_schema_version

REVISION = '1.0.45'
DOWN_REVISION = '1.0.44'


class Migration(migrations.Migration):
    """Migrate to add the extras column to the dbgroup table."""
    dependencies = [
        ('db', '0044_dbgroup_type_string'),
    ]

    operations = [
        migrations.AddField(
            model_name='dbgroup',
            name='extras',
            field=django.contrib.postgres.fields.jsonb.JSONField(default=dict, null=False),
        ),
        upgrade_schema_version(REVISION, DOWN_REVISION),
    ]
