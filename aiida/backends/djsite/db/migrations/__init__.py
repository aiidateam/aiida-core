# -*- coding: utf-8 -*-

__copyright__ = u"Copyright (c), This file is part of the AiiDA platform. For further information please visit http://www.aiida.net/.. All rights reserved."
__license__ = "MIT license, see LICENSE.txt file"
__version__ = "0.6.0.1"
__authors__ = "The AiiDA team."

LATEST_MIGRATION = '0002_db_state_change'


def _update_schema_version(version, apps, schema_editor):
    from aiida.backends.djsite.utils import set_db_schema_version
    set_db_schema_version(version)


def update_schema_version(version):
    from functools import partial
    from django.db import migrations

    return migrations.RunPython(partial(_update_schema_version, version))


def current_schema_version():
    # Have to use this ugly way of importing because the django migration
    # files start with numbers which are not a valid package name
    latest_migration = __import__(
        "aiida.backends.djsite.db.migrations.{}".format(LATEST_MIGRATION),
        fromlist=['SCHEMA_VERSION']
    )
    return latest_migration.SCHEMA_VERSION
