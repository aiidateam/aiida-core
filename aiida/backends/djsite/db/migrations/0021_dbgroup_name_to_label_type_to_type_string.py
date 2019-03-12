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
"""Migration that renames name and type columns to label and type_string"""

from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
from __future__ import absolute_import

# pylint: disable=no-name-in-module,import-error
from django.db import migrations
from aiida.backends.djsite.db.migrations import upgrade_schema_version

REVISION = '1.0.21'
DOWN_REVISION = '1.0.20'


class Migration(migrations.Migration):
    """Migration that renames name and type columns to label and type_string"""

    dependencies = [
        ('db', '0020_provenance_redesign'),
    ]

    operations = [
        migrations.RenameField(
            model_name='dbgroup',
            old_name='name',
            new_name='label',
        ),
        migrations.RenameField(
            model_name='dbgroup',
            old_name='type',
            new_name='type_string',
        ),
        migrations.AlterUniqueTogether(
            name='dbgroup',
            unique_together=set([('label', 'type_string')]),
        ),
        upgrade_schema_version(REVISION, DOWN_REVISION)
    ]
