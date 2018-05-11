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

from django.db import models, migrations
from aiida.backends.djsite.db.migrations import update_schema_version


SCHEMA_VERSION = "1.0.12"

class Migration(migrations.Migration):

    dependencies = [
        ('db', '0011_delete_kombu_tables'),
    ]

    operations = [
        migrations.DeleteModel(
            name='DbLock',
        ),
        update_schema_version(SCHEMA_VERSION)
    ]
