# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
# pylint: disable=invalid-name
"""Database migration."""
from django.db import migrations
from aiida.backends.djsite.db.migrations import upgrade_schema_version

REVISION = '1.0.12'
DOWN_REVISION = '1.0.11'


class Migration(migrations.Migration):
    """Database migration."""

    dependencies = [
        ('db', '0011_delete_kombu_tables'),
    ]

    operations = [migrations.DeleteModel(name='DbLock',), upgrade_schema_version(REVISION, DOWN_REVISION)]
