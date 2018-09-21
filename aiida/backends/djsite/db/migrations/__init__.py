# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
from __future__ import absolute_import

LATEST_MIGRATION = '0014_add_node_uuid_unique_constraint'


def _update_schema_version(version, apps, schema_editor):
    from aiida.backends.djsite.utils import set_db_schema_version
    set_db_schema_version(version)


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
        "aiida.backends.djsite.db.migrations.{}".format(LATEST_MIGRATION),
        fromlist=['REVISION']
    )
    return latest_migration.REVISION
