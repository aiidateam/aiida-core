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
"""Renaming `DbNode.type` to `DbNode.node_type`"""
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
from __future__ import absolute_import

# Remove when https://github.com/PyCQA/pylint/issues/1931 is fixed
# pylint: disable=no-name-in-module,import-error
from django.db import migrations
from aiida.backends.djsite.db.migrations import upgrade_schema_version

REVISION = '1.0.30'
DOWN_REVISION = '1.0.29'


class Migration(migrations.Migration):
    """Renaming `DbNode.type` to `DbNode.node_type`"""

    dependencies = [
        ('db', '0029_rename_parameter_data_to_dict'),
    ]

    operations = [
        migrations.RenameField(
            model_name='dbnode',
            old_name='type',
            new_name='node_type',
        ),
        upgrade_schema_version(REVISION, DOWN_REVISION)
    ]
