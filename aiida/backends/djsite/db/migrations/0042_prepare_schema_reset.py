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
"""Prepare the schema reset."""

# Remove when https://github.com/PyCQA/pylint/issues/1931 is fixed
# pylint: disable=no-name-in-module,import-error
from django.db import migrations
from aiida.backends.djsite.db.migrations import upgrade_schema_version

REVISION = '1.0.42'
DOWN_REVISION = '1.0.41'


class Migration(migrations.Migration):
    """Prepare the schema reset."""

    dependencies = [
        ('db', '0041_seal_unsealed_processes'),
    ]

    # The following statement is trying to perform an UPSERT, i.e. an UPDATE of a given key or if it doesn't exist fall
    # back to an INSERT. This problem is notoriously difficult to solve as explained in great detail in this article:
    # https://www.depesz.com/2012/06/10/why-is-upsert-so-complicated/ Postgres 9.5 provides an offical UPSERT method
    # through the `ON CONFLICT` keyword, but since we also support 9.4 we cannot use it here. The snippet used below
    # taken from the provided link, is not safe for concurrent operations, but since our migrations always run in an
    # isolated way, we do not suffer from those problems and can safely use it.
    operations = [
        migrations.RunSQL(
            sql=r"""
                INSERT INTO db_dbsetting (key, val, description, time)
                SELECT 'schema_generation', '"1"', 'Database schema generation', NOW()
                WHERE NOT EXISTS (SELECT * FROM db_dbsetting WHERE key = 'schema_generation');
                """,
            reverse_sql=''
        ),
        upgrade_schema_version(REVISION, DOWN_REVISION)
    ]
