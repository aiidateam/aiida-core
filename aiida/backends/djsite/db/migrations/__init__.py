# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

from aiida.backends.djsite.utils import SCHEMA_VERSION_DB_KEY, SCHEMA_VERSION_DB_DESCRIPTION


LATEST_MIGRATION = '0001_initial_schema_generation_2'


def _update_schema_version(version, apps, schema_editor):
    """
    The update schema uses the current models (and checks if the value is stored in EAV mode or JSONB)
    to avoid to use the DbSettings schema that may change (as it changed with the migration of the
    settings table to JSONB)
    """
    db_setting_model = apps.get_model('db', 'DbSetting')
    res = db_setting_model.objects.filter(key=SCHEMA_VERSION_DB_KEY).first()
    # If there is no schema record, create ones
    if res is None:
        res = db_setting_model()
        res.key = SCHEMA_VERSION_DB_KEY
        res.description = SCHEMA_VERSION_DB_DESCRIPTION

    res.val = str(version)

    # Store the final result
    res.save()


def _upgrade_schema_generation(version, apps, schema_editor):
    """
    The update schema uses the current models (and checks if the value is stored in EAV mode or JSONB)
    to avoid to use the DbSettings schema that may change (as it changed with the migration of the
    settings table to JSONB)
    """
    SCHEMA_GENERATION_KEY = 'schema_generation'
    db_setting_model = apps.get_model('db', 'DbSetting')
    res = db_setting_model.objects.filter(key=SCHEMA_GENERATION_KEY).first()
    # If there is no schema record, create ones
    if res is None:
        res = db_setting_model()
        res.key = SCHEMA_GENERATION_KEY
        res.description = 'Database schema generation'

    res.val = str(version)

    # Store the final result
    res.save()


def upgrade_schema_generation(schema_generation):
    from functools import partial
    from django.db import migrations
    return migrations.RunPython(partial(_upgrade_schema_generation, schema_generation))


def upgrade_schema_version(up_revision, down_revision):
    from functools import partial
    from django.db import migrations

    return migrations.RunPython(
        partial(_update_schema_version, up_revision),
        reverse_code=partial(_update_schema_version, down_revision))


def current_schema_version():
    # Have to use this ugly way of importing because the django migration
    # files start with numbers which are not a valid package name
    latest_migration = __import__(
        'aiida.backends.djsite.db.migrations.{}'.format(LATEST_MIGRATION),
        fromlist=['REVISION']
    )
    return latest_migration.REVISION
