# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
from __future__ import absolute_import

from django.db import models, migrations
from aiida.backends.djsite.db.migrations import upgrade_schema_version


REVISION = '1.0.10'
DOWN_REVISION = '1.0.9'


class Migration(migrations.Migration):

    dependencies = [
        ('db', '0009_base_data_plugin_type_string'),
    ]

    operations = [
        migrations.AddField(
            model_name='dbnode',
            name='process_type',
            field=models.CharField(max_length=255, db_index=True, null=True)
        ),
        upgrade_schema_version(REVISION, DOWN_REVISION)
    ]
