# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
from __future__ import unicode_literals

import django_extensions.db.fields
from django.db import migrations

from aiida.backends.djsite.db.migrations import update_schema_version


SCHEMA_VERSION = "1.0.5"


class Migration(migrations.Migration):
    dependencies = [
        ('db', '0004_add_daemon_and_uuid_indices'),
    ]

    operations = [
        # Create the index that speeds up the daemon queries
        # We use the RunSQL command because Django interface
        # doesn't seem to support partial indexes
        migrations.RunSQL("""
            DROP TRIGGER IF EXISTS autoupdate_tc ON db_dblink;
            DROP FUNCTION IF EXISTS update_tc();
            DROP TABLE db_dbpath; 
        """),
        update_schema_version(SCHEMA_VERSION)
    ]
