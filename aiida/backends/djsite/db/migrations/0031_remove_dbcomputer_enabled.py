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
"""Remove `DbComputer.enabled`"""

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
