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
"""Simplify the `DbUser` model."""

# Remove when https://github.com/PyCQA/pylint/issues/1931 is fixed
# pylint: disable=no-name-in-module,import-error,no-member
from django.db import migrations, models

from aiida.backends.djsite.db.migrations import upgrade_schema_version

REVISION = '1.0.35'
DOWN_REVISION = '1.0.34'


class Migration(migrations.Migration):
    """Simplify the `DbUser` model by dropping unused columns."""

    dependencies = [
        ('db', '0034_drop_node_columns_nodeversion_public'),
    ]

    operations = [
        migrations.AlterField(
            model_name='dbuser',
            name='password',
            field=models.CharField(max_length=128, default='pass', verbose_name='password'),
        ),
        migrations.RemoveField(
            model_name='dbuser',
            name='password',
        ),
        migrations.RemoveField(
            model_name='dbuser',
            name='date_joined',
        ),
        migrations.RemoveField(
            model_name='dbuser',
            name='groups',
        ),
        migrations.RemoveField(
            model_name='dbuser',
            name='is_active',
        ),
        migrations.RemoveField(
            model_name='dbuser',
            name='is_staff',
        ),
        migrations.AlterField(
            model_name='dbuser',
            name='is_superuser',
            field=models.BooleanField(default=False, blank=True),
        ),
        migrations.RemoveField(
            model_name='dbuser',
            name='is_superuser',
        ),
        migrations.RemoveField(
            model_name='dbuser',
            name='last_login',
        ),
        migrations.RemoveField(
            model_name='dbuser',
            name='user_permissions',
        ),
        upgrade_schema_version(REVISION, DOWN_REVISION)
    ]
