# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
# pylint: disable=invalid-name,too-few-public-methods
"""Drop the `transport_params` from the `Computer` database model."""

# Remove when https://github.com/PyCQA/pylint/issues/1931 is fixed
# pylint: disable=no-name-in-module,import-error,no-member
from django.db import migrations

from aiida.backends.djsite.db.migrations import upgrade_schema_version

REVISION = '1.0.36'
DOWN_REVISION = '1.0.35'


class Migration(migrations.Migration):
    """Drop the `transport_params` from the `Computer` database model."""

    dependencies = [
        ('db', '0035_simplify_user_model'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='dbcomputer',
            name='transport_params',
        ),
        upgrade_schema_version(REVISION, DOWN_REVISION)
    ]
