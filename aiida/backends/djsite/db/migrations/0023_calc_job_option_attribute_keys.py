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
"""Migration of ProcessNode attributes for metadata options whose key changed."""

# Remove when https://github.com/PyCQA/pylint/issues/1931 is fixed
# pylint: disable=no-name-in-module,import-error
from django.db import migrations

from aiida.backends.djsite.db.migrations import upgrade_schema_version

REVISION = '1.0.23'
DOWN_REVISION = '1.0.22'


class Migration(migrations.Migration):
    """Migration of ProcessNode attributes for metadata options whose key changed.

    Renamed attribute keys:

      * `custom_environment_variables` -> `environment_variables` (CalcJobNode)
      * `jobresource_params` -> `resources` (CalcJobNode)
      * `_process_label` -> `process_label` (ProcessNode)
      * `parser` -> `parser_name` (CalcJobNode)

    Deleted attributes:
      * `linkname_retrieved` (We do not actually delete it just in case some relies on it)

    """

    dependencies = [
        ('db', '0022_dbgroup_type_string_change_content'),
    ]

    operations = [
        migrations.RunSQL(
            sql=r"""
            UPDATE db_dbattribute AS attribute
            SET key =  regexp_replace(attribute.key, '^custom_environment_variables', 'environment_variables')
            FROM db_dbnode AS node
            WHERE
                (
                    attribute.key = 'custom_environment_variables' OR
                    attribute.key LIKE 'custom\_environment\_variables.%'
                ) AND
                node.type = 'node.process.calculation.calcjob.CalcJobNode.' AND
                node.id = attribute.dbnode_id;
            -- custom_environment_variables -> environment_variables

            UPDATE db_dbattribute AS attribute
            SET key =  regexp_replace(attribute.key, '^jobresource_params', 'resources')
            FROM db_dbnode AS node
            WHERE
                (
                    attribute.key = 'jobresource_params' OR
                    attribute.key LIKE 'jobresource\_params.%'
                ) AND
                node.type = 'node.process.calculation.calcjob.CalcJobNode.' AND
                node.id = attribute.dbnode_id;
            -- jobresource_params -> resources

            UPDATE db_dbattribute AS attribute
            SET key =  regexp_replace(attribute.key, '^_process_label', 'process_label')
            FROM db_dbnode AS node
            WHERE
                attribute.key = '_process_label' AND
                node.type LIKE 'node.process.%' AND
                node.id = attribute.dbnode_id;
            -- _process_label -> process_label

            UPDATE db_dbattribute AS attribute
            SET key =  regexp_replace(attribute.key, '^parser', 'parser_name')
            FROM db_dbnode AS node
            WHERE
                attribute.key = 'parser' AND
                node.type = 'node.process.calculation.calcjob.CalcJobNode.' AND
                node.id = attribute.dbnode_id;
            -- parser -> parser_name
            """,
            reverse_sql=r"""
            UPDATE db_dbattribute AS attribute
            SET key =  regexp_replace(attribute.key, '^environment_variables', 'custom_environment_variables')
            FROM db_dbnode AS node
            WHERE
                (
                    attribute.key = 'environment_variables' OR
                    attribute.key LIKE 'environment\_variables.%'
                ) AND
                node.type = 'node.process.calculation.calcjob.CalcJobNode.' AND
                node.id = attribute.dbnode_id;
            -- environment_variables -> custom_environment_variables

            UPDATE db_dbattribute AS attribute
            SET key =  regexp_replace(attribute.key, '^resources', 'jobresource_params')
            FROM db_dbnode AS node
            WHERE
                (
                    attribute.key = 'resources' OR
                    attribute.key LIKE 'resources.%'
                ) AND
                node.type = 'node.process.calculation.calcjob.CalcJobNode.' AND
                node.id = attribute.dbnode_id;
            -- resources -> jobresource_params

            UPDATE db_dbattribute AS attribute
            SET key =  regexp_replace(attribute.key, '^process_label', '_process_label')
            FROM db_dbnode AS node
            WHERE
                attribute.key = 'process_label' AND
                node.type LIKE 'node.process.%' AND
                node.id = attribute.dbnode_id;
            -- process_label -> _process_label

            UPDATE db_dbattribute AS attribute
            SET key =  regexp_replace(attribute.key, '^parser_name', 'parser')
            FROM db_dbnode AS node
            WHERE
                attribute.key = 'parser_name' AND
                node.type = 'node.process.calculation.calcjob.CalcJobNode.' AND
                node.id = attribute.dbnode_id;
            -- parser_name -> parser
            """
        ),
        upgrade_schema_version(REVISION, DOWN_REVISION)
    ]
