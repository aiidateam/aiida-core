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


SCHEMA_VERSION = "1.0.4"


class Migration(migrations.Migration):
    dependencies = [
        ('db', '0003_add_link_type'),
    ]

    operations = [
        # Create the index that speeds up the daemon queries
        # We use the RunSQL command because Django interface
        # doesn't seem to support partial indexes
        migrations.RunSQL("""
        CREATE INDEX tval_idx_for_daemon
        ON db_dbattribute (tval)
        WHERE ("db_dbattribute"."tval"
        IN ('COMPUTED', 'WITHSCHEDULER', 'TOSUBMIT'))"""),

        # Create an index on UUIDs to speed up loading of nodes
        # using this field
        migrations.AlterField(
            model_name='dbnode',
            name='uuid',
            field=django_extensions.db.fields.UUIDField(db_index=True,
                                                        editable=False,
                                                        blank=True),
            preserve_default=True,
        ),
        update_schema_version(SCHEMA_VERSION)
    ]
