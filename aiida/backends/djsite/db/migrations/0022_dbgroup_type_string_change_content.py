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
"""Migration after the update of group_types"""

from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
from __future__ import absolute_import

# pylint: disable=no-name-in-module,import-error
from django.db import migrations
from aiida.backends.djsite.db.migrations import upgrade_schema_version

REVISION = '1.0.22'
DOWN_REVISION = '1.0.21'

forward_sql = [
    """UPDATE db_dbgroup SET type_string = 'user' WHERE type_string = '';""",
    """UPDATE db_dbgroup SET type_string = 'data.upf' WHERE type_string = 'data.upf.family';""",
    """UPDATE db_dbgroup SET type_string = 'auto.import' WHERE type_string = 'aiida.import';""",
    """UPDATE db_dbgroup SET type_string = 'auto.run' WHERE type_string = 'autogroup.run';""",
]

reverse_sql = [
    """UPDATE db_dbgroup SET type_string = '' WHERE type_string = 'user';""",
    """UPDATE db_dbgroup SET type_string = 'data.upf.family' WHERE type_string = 'data.upf';""",
    """UPDATE db_dbgroup SET type_string = 'aiida.import' WHERE type_string = 'auto.import';""",
    """UPDATE db_dbgroup SET type_string = 'autogroup.run' WHERE type_string = 'auto.run';""",
]


class Migration(migrations.Migration):
    """Migration after the update of group_types"""
    dependencies = [
        ('db', '0021_dbgroup_name_to_label_type_to_type_string'),
    ]

    operations = [
        migrations.RunSQL(sql='\n'.join(forward_sql), reverse_sql='\n'.join(reverse_sql)),
        upgrade_schema_version(REVISION, DOWN_REVISION),
    ]
