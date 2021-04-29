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
"""Rename the ``name`` column of the ``Computer`` entity to ``label``."""
from django.db import migrations

from aiida.backends.djsite.db.migrations import upgrade_schema_version

REVISION = '1.0.48'
DOWN_REVISION = '1.0.47'


class Migration(migrations.Migration):
    """Rename the ``name`` column of the ``Computer`` entity to ``label``."""

    dependencies = [
        ('db', '0047_migrate_repository'),
    ]

    operations = [
        migrations.RenameField(
            model_name='dbcomputer',
            old_name='name',
            new_name='label',
        ),
        upgrade_schema_version(REVISION, DOWN_REVISION),
    ]
