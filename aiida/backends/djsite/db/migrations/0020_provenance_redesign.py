# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
# pylint: disable=invalid-name,too-few-public-methods,unused-argument
"""Migration after the provenance redesign"""

from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
from __future__ import absolute_import

# Remove when https://github.com/PyCQA/pylint/issues/1931 is fixed
# pylint: disable=no-name-in-module,import-error
from django.db import migrations
from aiida.backends.djsite.db.migrations import upgrade_schema_version

REVISION = '1.0.20'
DOWN_REVISION = '1.0.19'


def migrate_infer_calculation_entry_point(apps, schema_editor):
    """Set the process type for calculation nodes by inferring it from their type string."""
    from aiida.manage.database.integrity import write_database_integrity_violation
    from aiida.manage.database.integrity.plugins import infer_calculation_entry_point
    from aiida.plugins.entry_point import ENTRY_POINT_STRING_SEPARATOR

    fallback_cases = []
    DbNode = apps.get_model('db', 'DbNode')

    type_strings = DbNode.objects.filter(type__startswith='calculation.').values_list('type', flat=True)
    mapping_node_type_to_entry_point = infer_calculation_entry_point(type_strings=type_strings)

    for type_string, entry_point_string in mapping_node_type_to_entry_point.items():

        # If the entry point string does not contain the entry point string separator, the mapping function was not able
        # to map the type string onto a known entry point string. As a fallback it uses the modified type string itself.
        # All affected entries should be logged to file that the user can consult.
        if ENTRY_POINT_STRING_SEPARATOR not in entry_point_string:
            query_set = DbNode.objects.filter(type=type_string).values_list('uuid')
            uuids = [str(entry[0]) for entry in query_set]
            for uuid in uuids:
                fallback_cases.append([uuid, type_string, entry_point_string])

        DbNode.objects.filter(type=type_string).update(process_type=entry_point_string)

    if fallback_cases:
        headers = ['UUID', 'type (old)', 'process_type (fallback)']
        warning_message = 'found calculation nodes with a type string that could not be mapped onto a known entry point'
        action_message = 'inferred `process_type` for all calculation nodes, using fallback for unknown entry points'
        write_database_integrity_violation(fallback_cases, headers, warning_message, action_message)


def detect_unexpected_links(apps, schema_editor):
    """Scan the database for any links that are unexpected.

    The checks will verify that there are no outgoing `call` or `return` links from calculation nodes and that if a
    workflow node has a `create` link, it has at least an accompanying return link to the same data node, or it has a
    `call` link to a calculation node that takes the created data node as input.
    """
    from aiida.backends.general.migrations.provenance_redesign import INVALID_LINK_SELECT_STATEMENTS
    from aiida.manage.database.integrity import write_database_integrity_violation

    with schema_editor.connection.cursor() as cursor:

        for sql, warning_message in INVALID_LINK_SELECT_STATEMENTS:
            cursor.execute(sql)
            results = cursor.fetchall()
            if results:
                headers = ['UUID source', 'UUID target', 'link type', 'link label']
                write_database_integrity_violation(results, headers, warning_message)


def reverse_code(apps, schema_editor):
    """Reversing the inference of the process type is not possible and not necessary."""


class Migration(migrations.Migration):
    """Migration to effectuate changes introduced by the provenance redesign

    This includes in order:

        * Rename the type column of process nodes
        * Remove illegal links
        * Rename link types

    The exact reverse operation is not possible because the renaming of the type string of `JobCalculation` nodes is
    done in a lossy way. Originally this type string contained the exact sub class of the `JobCalculation` but in the
    migration this is changed to always be `node.process.calculation.calcjob.CalcJobNode.`. In the reverse operation,
    this can then only be reset to `calculation.job.JobCalculation.` but the information on the exact sub class is lost.
    """
    dependencies = [
        ('db', '0019_migrate_builtin_calculations'),
    ]

    operations = [
        migrations.RunPython(migrate_infer_calculation_entry_point, reverse_code=reverse_code, atomic=True),
        migrations.RunPython(detect_unexpected_links, reverse_code=reverse_code, atomic=True),
        migrations.RunSQL(
            """
            DELETE FROM db_dblink WHERE db_dblink.id IN (
                SELECT db_dblink.id FROM db_dblink
                INNER JOIN db_dbnode ON db_dblink.input_id = db_dbnode.id
                WHERE
                    (db_dbnode.type LIKE 'calculation.job%' OR db_dbnode.type LIKE 'calculation.inline%')
                    AND db_dblink.type = 'returnlink'
            ); -- Delete all outgoing RETURN links from JobCalculation and InlineCalculation nodes

            DELETE FROM db_dblink WHERE db_dblink.id IN (
                SELECT db_dblink.id FROM db_dblink
                INNER JOIN db_dbnode ON db_dblink.input_id = db_dbnode.id
                WHERE
                    (db_dbnode.type LIKE 'calculation.job%' OR db_dbnode.type LIKE 'calculation.inline%')
                    AND db_dblink.type = 'calllink'
            ); -- Delete all outgoing CALL links from JobCalculation and InlineCalculation nodes

            DELETE FROM db_dblink WHERE db_dblink.id IN (
                SELECT db_dblink.id FROM db_dblink
                INNER JOIN db_dbnode ON db_dblink.input_id = db_dbnode.id
                WHERE
                    (db_dbnode.type LIKE 'calculation.function%' OR db_dbnode.type LIKE 'calculation.work%')
                    AND db_dblink.type = 'createlink'
            ); -- Delete all outgoing CREATE links from FunctionCalculation and WorkCalculation nodes

            UPDATE db_dbnode SET type = 'calculation.work.WorkCalculation.'
            WHERE type = 'calculation.process.ProcessCalculation.';
             -- First migrate very old `ProcessCalculation` to `WorkCalculation`

            UPDATE db_dbnode SET type = 'node.process.workflow.workfunction.WorkFunctionNode.' FROM db_dbattribute
            WHERE db_dbattribute.dbnode_id = db_dbnode.id
                AND type = 'calculation.work.WorkCalculation.'
                AND db_dbattribute.key = 'function_name';
             -- WorkCalculations that have a `function_name` attribute are FunctionCalculations

            UPDATE db_dbnode SET type = 'node.process.workflow.workchain.WorkChainNode.'
            WHERE type = 'calculation.work.WorkCalculation.';
             -- Update type for `WorkCalculation` nodes - all what is left should be `WorkChainNodes`

            UPDATE db_dbnode SET type = 'node.process.calculation.calcjob.CalcJobNode.'
            WHERE type LIKE 'calculation.job.%'; -- Update type for JobCalculation nodes

            UPDATE db_dbnode SET type = 'node.process.calculation.calcfunction.CalcFunctionNode.'
            WHERE type = 'calculation.inline.InlineCalculation.'; -- Update type for InlineCalculation nodes

            UPDATE db_dbnode SET type = 'node.process.workflow.workfunction.WorkFunctionNode.'
            WHERE type = 'calculation.function.FunctionCalculation.'; -- Update type for FunctionCalculation nodes

            UPDATE db_dblink SET type = 'create' WHERE type = 'createlink'; -- Rename `createlink` to `create`
            UPDATE db_dblink SET type = 'return' WHERE type = 'returnlink'; -- Rename `returnlink` to `return`

            UPDATE db_dblink SET type = 'input_calc' FROM db_dbnode
            WHERE db_dblink.output_id = db_dbnode.id AND db_dbnode.type LIKE 'node.process.calculation%'
            AND db_dblink.type = 'inputlink';
             -- Rename `inputlink` to `input_calc` if the target node is a calculation type node

            UPDATE db_dblink SET type = 'input_work' FROM db_dbnode
            WHERE db_dblink.output_id = db_dbnode.id AND db_dbnode.type LIKE 'node.process.workflow%'
            AND db_dblink.type = 'inputlink';
             -- Rename `inputlink` to `input_work` if the target node is a workflow type node

            UPDATE db_dblink SET type = 'call_calc' FROM db_dbnode
            WHERE db_dblink.output_id = db_dbnode.id AND db_dbnode.type LIKE 'node.process.calculation%'
            AND db_dblink.type = 'calllink';
             -- Rename `calllink` to `call_calc` if the target node is a calculation type node

            UPDATE db_dblink SET type = 'call_work' FROM db_dbnode
            WHERE db_dblink.output_id = db_dbnode.id AND db_dbnode.type LIKE 'node.process.workflow%'
            AND db_dblink.type = 'calllink';
             -- Rename `calllink` to `call_work` if the target node is a workflow type node

            """,
            reverse_sql="""
            UPDATE db_dbnode SET type = 'calculation.job.JobCalculation.'
            WHERE type = 'node.process.calculation.calcjob.CalcJobNode.';

            UPDATE db_dbnode SET type = 'calculatison.inline.InlineCalculation.'
            WHERE type = 'node.process.calculation.calcfunction.CalcFunctionNode.';

            UPDATE db_dbnode SET type = 'calculation.function.FunctionCalculation.'
            WHERE type = 'node.process.workflow.workfunction.WorkFunctionNode.';

            UPDATE db_dbnode SET type = 'calculation.work.WorkCalculation.'
            WHERE type = 'node.process.workflow.workchain.WorkChainNode.';


            UPDATE db_dblink SET type = 'inputlink'
            WHERE type = 'input_call' OR type = 'input_work';

            UPDATE db_dblink SET type = 'calllink'
            WHERE type = 'call_call' OR type = 'call_work';

            UPDATE db_dblink SET type = 'createlink'
            WHERE type = 'create';

            UPDATE db_dblink SET type = 'returnlink'
            WHERE type = 'return';

            """),
        upgrade_schema_version(REVISION, DOWN_REVISION)
    ]
