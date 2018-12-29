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
import aiida.common.timezone
from aiida.backends.djsite.db.migrations import upgrade_schema_version


REVISION = '1.0.5'
DOWN_REVISION = '1.0.4'


class Migration(migrations.Migration):

    dependencies = [
        ('db', '0004_add_daemon_and_uuid_indices'),
    ]

    operations = [
        migrations.AlterField(
            model_name='dbnode',
            name='ctime',
            field=models.DateTimeField(default=aiida.common.timezone.now, editable=False, db_index=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='dbnode',
            name='mtime',
            field=models.DateTimeField(auto_now=True, db_index=True),
            preserve_default=True,
        ),
        upgrade_schema_version(REVISION, DOWN_REVISION)
    ]
