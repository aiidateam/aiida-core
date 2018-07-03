# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
# pylint: disable=invalid-name
"""Add a uniqueness constraint to the uuid column of DbNode table."""
from __future__ import unicode_literals
from __future__ import absolute_import

from django.db import migrations
from django_extensions.db.fields import UUIDField
from aiida.backends.djsite.db.migrations import update_schema_version
from aiida.backends.settings import AIIDANODES_UUID_VERSION

SCHEMA_VERSION = "1.0.14"


class Migration(migrations.Migration):
    """Add a uniqueness constraint to the uuid column of DbNode table."""

    dependencies = [
        ('db', '0013_django_1_8'),
    ]

    operations = [
        migrations.AlterField(
            model_name='dbnode',
            name='uuid',
            field=UUIDField(auto=True, version=AIIDANODES_UUID_VERSION, unique=True),
        ),
        update_schema_version(SCHEMA_VERSION)
    ]
