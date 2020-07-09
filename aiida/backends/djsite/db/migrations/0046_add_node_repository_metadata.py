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
"""Migration to add the `repository_metadata` JSONB column."""

# pylint: disable=no-name-in-module,import-error
import django.contrib.postgres.fields.jsonb
from django.db import migrations
from aiida.backends.djsite.db.migrations import upgrade_schema_version

REVISION = '1.0.46'
DOWN_REVISION = '1.0.45'


class Migration(migrations.Migration):
    """Migration to add the `repository_metadata` JSONB column."""

    dependencies = [
        ('db', '0045_dbgroup_extras'),
    ]

    operations = [
        migrations.AddField(
            model_name='dbnode',
            name='repository_metadata',
            field=django.contrib.postgres.fields.jsonb.JSONField(null=True),
        ),
        upgrade_schema_version(REVISION, DOWN_REVISION),
    ]
