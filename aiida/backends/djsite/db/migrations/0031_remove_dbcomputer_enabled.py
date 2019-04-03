# -*- coding: utf-8 -*-
# pylint: disable=invalid-name,too-few-public-methods
"""Remove `DbComputer.enabled`"""
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
from __future__ import absolute_import

# Remove when https://github.com/PyCQA/pylint/issues/1931 is fixed
# pylint: disable=no-name-in-module,import-error
from django.db import migrations
from aiida.backends.djsite.db.migrations import upgrade_schema_version

REVISION = '1.0.31'
DOWN_REVISION = '1.0.30'


class Migration(migrations.Migration):
    """Remove `DbComputer.enabled`"""

    dependencies = [
        ('db', '0030_dbnode_type_to_dbnode_node_type'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='dbcomputer',
            name='enabled',
        ),
        upgrade_schema_version(REVISION, DOWN_REVISION)
    ]
