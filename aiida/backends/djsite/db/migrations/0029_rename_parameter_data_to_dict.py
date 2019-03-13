# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
# pylint: disable=invalid-name,too-few-public-methods
"""Data migration for after `ParameterData` was renamed to `Dict`."""
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
from __future__ import absolute_import

# Remove when https://github.com/PyCQA/pylint/issues/1931 is fixed
# pylint: disable=no-name-in-module,import-error
from django.db import migrations
from aiida.backends.djsite.db.migrations import upgrade_schema_version

REVISION = '1.0.29'
DOWN_REVISION = '1.0.28'


class Migration(migrations.Migration):
    """Data migration for after `ParameterData` was renamed to `Dict`."""

    dependencies = [
        ('db', '0028_remove_node_prefix'),
    ]

    operations = [
        migrations.RunSQL(
            sql=r"""UPDATE db_dbnode SET type = 'data.dict.Dict.' WHERE type = 'data.parameter.ParameterData.';""",
            reverse_sql=
            r"""UPDATE db_dbnode SET type = 'data.parameter.ParameterData.' WHERE type = 'data.dict.Dict.';"""),
        upgrade_schema_version(REVISION, DOWN_REVISION)
    ]
