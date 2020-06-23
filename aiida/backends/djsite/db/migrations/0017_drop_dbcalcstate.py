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

REVISION = '1.0.17'
DOWN_REVISION = '1.0.16'


class Migration(migrations.Migration):
    """Database migration."""

    dependencies = [
        ('db', '0016_code_sub_class_of_data'),
    ]

    operations = [migrations.DeleteModel(name='DbCalcState',), upgrade_schema_version(REVISION, DOWN_REVISION)]
