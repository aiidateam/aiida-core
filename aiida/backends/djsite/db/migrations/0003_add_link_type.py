# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import aiida.utils.timezone
from aiida.backends.djsite.db.migrations import update_schema_version


__copyright__ = u"Copyright (c), This file is part of the AiiDA platform. For further information please visit http://www.aiida.net/. All rights reserved."
__license__ = "MIT license, see LICENSE.txt file."
__authors__ = "The AiiDA team."
__version__ = "0.7.0.1"

SCHEMA_VERSION = "1.0.3"


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
            field=models.DateTimeField(default=aiida.utils.timezone.now, editable=False),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='dbcomment',
            name='ctime',
            field=models.DateTimeField(default=aiida.utils.timezone.now, editable=False),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='dbgroup',
            name='time',
            field=models.DateTimeField(default=aiida.utils.timezone.now, editable=False),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='dblock',
            name='creation',
            field=models.DateTimeField(default=aiida.utils.timezone.now, editable=False),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='dblog',
            name='time',
            field=models.DateTimeField(default=aiida.utils.timezone.now, editable=False),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='dbnode',
            name='ctime',
            field=models.DateTimeField(default=aiida.utils.timezone.now, editable=False),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='dbuser',
            name='date_joined',
            field=models.DateTimeField(default=aiida.utils.timezone.now),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='dbworkflow',
            name='ctime',
            field=models.DateTimeField(default=aiida.utils.timezone.now, editable=False),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='dbworkflowdata',
            name='time',
            field=models.DateTimeField(default=aiida.utils.timezone.now, editable=False),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='dbworkflowstep',
            name='time',
            field=models.DateTimeField(default=aiida.utils.timezone.now, editable=False),
            preserve_default=True,
        ),
        migrations.AlterUniqueTogether(
            name='dblink',
            unique_together=set([]),
        ),
        update_schema_version(SCHEMA_VERSION)
    ]
