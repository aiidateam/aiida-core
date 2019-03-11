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
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
from __future__ import absolute_import

from django.db import migrations, models
from aiida.backends.djsite.db.migrations import upgrade_schema_version
from aiida.common.utils import get_new_uuid

REVISION = '1.0.14'
DOWN_REVISION = '1.0.13'


def verify_node_uuid_uniqueness(apps, schema_editor):
    """Check whether the database contains nodes with duplicate UUIDS.

    Note that we have to redefine this method from aiida.manage.database.integrity.verify_node_uuid_uniqueness
    because the migrations.RunPython command that will invoke this function, will pass two arguments and therefore
    this wrapper needs to have a different function signature.

    :raises: IntegrityError if database contains nodes with duplicate UUIDS.
    """
    from aiida.manage.database.integrity.duplicate_uuid import verify_uuid_uniqueness
    verify_uuid_uniqueness(table='db_dbnode')


def reverse_code(apps, schema_editor):
    pass


class Migration(migrations.Migration):
    """Add a uniqueness constraint to the uuid column of DbNode table."""

    dependencies = [
        ('db', '0013_django_1_8'),
    ]

    operations = [
        migrations.RunPython(verify_node_uuid_uniqueness, reverse_code=reverse_code),
        migrations.AlterField(
            model_name='dbnode',
            name='uuid',
            field=models.CharField(max_length=36, default=get_new_uuid, unique=True),
        ),
        upgrade_schema_version(REVISION, DOWN_REVISION)
    ]
