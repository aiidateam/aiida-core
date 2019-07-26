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

from aiida.backends.manager import SCHEMA_VERSION_KEY, SCHEMA_VERSION_DESCRIPTION, SCHEMA_GENERATION_KEY, SCHEMA_GENERATION_DESCRIPTION


LATEST_MIGRATION = '0001_initial_schema_generation_2'


def _update_schema_version(version, apps, schema_editor):
    """
    The update schema uses the current models (and checks if the value is stored in EAV mode or JSONB)
    to avoid to use the DbSettings schema that may change (as it changed with the migration of the
    settings table to JSONB)
    """
    db_setting_model = apps.get_model('db', 'DbSetting')
    result = db_setting_model.objects.filter(key=SCHEMA_VERSION_KEY).first()
    # If there is no schema record, create ones
    if result is None:
        result = db_setting_model()
        result.key = SCHEMA_VERSION_KEY
        result.description = SCHEMA_VERSION_DESCRIPTION

    result.val = str(version)
    result.save()


def _upgrade_schema_generation(version, apps, schema_editor):
    """
    The update schema uses the current models (and checks if the value is stored in EAV mode or JSONB)
    to avoid to use the DbSettings schema that may change (as it changed with the migration of the
    settings table to JSONB)
    """
    db_setting_model = apps.get_model('db', 'DbSetting')
    result = db_setting_model.objects.filter(key=SCHEMA_GENERATION_KEY).first()
    # If there is no schema record, create ones
    if result is None:
        result = db_setting_model()
        result.key = SCHEMA_GENERATION_KEY
        result.description = SCHEMA_GENERATION_DESCRIPTION

    result.val = str(version)
    result.save()


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
