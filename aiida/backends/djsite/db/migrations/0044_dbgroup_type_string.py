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
"""Migration after the `Group` class became pluginnable and so the group `type_string` changed."""

# pylint: disable=no-name-in-module,import-error
from django.db import migrations
from aiida.backends.djsite.db.migrations import upgrade_schema_version

REVISION = '1.0.44'
DOWN_REVISION = '1.0.43'

forward_sql = [
    """UPDATE db_dbgroup SET type_string = 'core' WHERE type_string = 'user';""",
    """UPDATE db_dbgroup SET type_string = 'core.upf' WHERE type_string = 'data.upf';""",
    """UPDATE db_dbgroup SET type_string = 'core.import' WHERE type_string = 'auto.import';""",
    """UPDATE db_dbgroup SET type_string = 'core.auto' WHERE type_string = 'auto.run';""",
]

reverse_sql = [
    """UPDATE db_dbgroup SET type_string = 'user' WHERE type_string = 'core';""",
    """UPDATE db_dbgroup SET type_string = 'data.upf' WHERE type_string = 'core.upf';""",
    """UPDATE db_dbgroup SET type_string = 'auto.import' WHERE type_string = 'core.import';""",
    """UPDATE db_dbgroup SET type_string = 'auto.run' WHERE type_string = 'core.auto';""",
]


class Migration(migrations.Migration):
    """Migration after the update of group `type_string`"""
    dependencies = [
        ('db', '0043_default_link_label'),
    ]

    operations = [
        migrations.RunSQL(sql='\n'.join(forward_sql), reverse_sql='\n'.join(reverse_sql)),
        upgrade_schema_version(REVISION, DOWN_REVISION),
    ]
