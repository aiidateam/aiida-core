# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################


LATEST_MIGRATION = '0004_add_daemon_and_uuid_indices'


def _update_schema_version(version, apps, schema_editor):
    from aiida.backends.utils import set_db_schema_version
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
