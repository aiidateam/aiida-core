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


REVISION = '1.0.3'
DOWN_REVISION = '1.0.2'


class Migration(migrations.Migration):

    dependencies = [
        ('db', '0002_db_state_change'),
    ]

    operations = [
        migrations.AddField(
            model_name='dblink',
            name='type',
            field=models.CharField(db_index=True, max_length=255, blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='dbcalcstate',
            name='time',
            field=models.DateTimeField(default=aiida.common.timezone.now, editable=False),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='dbcomment',
            name='ctime',
            field=models.DateTimeField(default=aiida.common.timezone.now, editable=False),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='dbgroup',
            name='time',
            field=models.DateTimeField(default=aiida.common.timezone.now, editable=False),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='dblock',
            name='creation',
            field=models.DateTimeField(default=aiida.common.timezone.now, editable=False),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='dblog',
            name='time',
            field=models.DateTimeField(default=aiida.common.timezone.now, editable=False),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='dbnode',
            name='ctime',
            field=models.DateTimeField(default=aiida.common.timezone.now, editable=False),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='dbuser',
            name='date_joined',
            field=models.DateTimeField(default=aiida.common.timezone.now),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='dbworkflow',
            name='ctime',
            field=models.DateTimeField(default=aiida.common.timezone.now, editable=False),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='dbworkflowdata',
            name='time',
            field=models.DateTimeField(default=aiida.common.timezone.now, editable=False),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='dbworkflowstep',
            name='time',
            field=models.DateTimeField(default=aiida.common.timezone.now, editable=False),
            preserve_default=True,
        ),
        migrations.AlterUniqueTogether(
            name='dblink',
            unique_together=set([]),
        ),
        upgrade_schema_version(REVISION, DOWN_REVISION)
    ]
