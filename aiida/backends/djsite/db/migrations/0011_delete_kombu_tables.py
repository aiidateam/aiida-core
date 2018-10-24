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

from django.db import migrations
from aiida.backends.djsite.db.migrations import upgrade_schema_version


REVISION = '1.0.11'
DOWN_REVISION = '1.0.10'


class Migration(migrations.Migration):

    dependencies = [
        ('db', '0010_process_type'),
    ]

    operations = [
        migrations.RunSQL("""
            DROP TABLE IF EXISTS kombu_message;
            DROP TABLE IF EXISTS kombu_queue;
            DELETE FROM db_dbsetting WHERE key = 'daemon|user';
            DELETE FROM db_dbsetting WHERE key = 'daemon|task_stop|retriever';
            DELETE FROM db_dbsetting WHERE key = 'daemon|task_start|retriever';
            DELETE FROM db_dbsetting WHERE key = 'daemon|task_stop|updater';
            DELETE FROM db_dbsetting WHERE key = 'daemon|task_start|updater';
            DELETE FROM db_dbsetting WHERE key = 'daemon|task_stop|submitter';
            DELETE FROM db_dbsetting WHERE key = 'daemon|task_start|submitter';
        """),
        upgrade_schema_version(REVISION, DOWN_REVISION)
    ]
