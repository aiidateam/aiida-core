# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Migrate attributes from old InlineCalculation that have been transformed into CalcFunctions:

* OLD `sealed` and `function_name` remain the same
* OLD `namespace` becomes `function_namespace`
* OLD `first_line_source_code` becomes `function_starting_line_number`
* OLD `source_file` is moved to repository and dropped from DB
* OLD `source_code` is used to calculate `function_number_of_lines` and dropped from DB
* NEW `exit_status` is initialized at 0
* NEW `process_state` is initialized at "finished"
* NEW `process_label` is set as `Legacy InlineCalculation`

Note 1: old InlineCalculation can be identified by the old keywords, and after migration they will be
identified by having `function_number_of_lines` but no `version`.

Note 2: `exit_status` and `process_state` are initialized to 0 and "finished" respectively because the
CalcFunctions affected are old InlineCalculation, which were only stored if they succeeded. You can check
the relevant code here (line 60 has the execution call, it is stored after that):

https://github.com/aiidateam/aiida-core/blob/v0.12.5/aiida/orm/implementation/django/calculation/inline.py#L60
"""
# pylint: disable=invalid-name
from django.db import migrations, transaction

from aiida.backends.general.migrations import utils
from aiida.backends.djsite.db.migrations import upgrade_schema_version

REVISION = '1.0.46'
DOWN_REVISION = '1.0.45'


def create_new_attributes(apps, _):
    """Creates the new attributes"""
    DbNode = apps.get_model('db', 'DbNode')

    with transaction.atomic():
        inline_type = 'process.calculation.calcfunction.CalcFunctionNode.'
        inline_nodes = DbNode.objects.filter(node_type=inline_type, attributes__has_key='namespace')

        for inline_node in inline_nodes:
            inline_node.attributes['function_namespace'] = inline_node.attributes['namespace']
            inline_node.attributes['function_starting_line_number'] = inline_node.attributes['first_line_source_code']
            inline_node.attributes['function_number_of_lines'] = len(inline_node.attributes['source_code'].splitlines())
            inline_node.attributes['process_label'] = 'Legacy InlineCalculation'
            inline_node.attributes['process_state'] = 'finished'
            inline_node.attributes['exit_status'] = 0

            utils.put_object_from_string(inline_node.uuid, 'source_file', inline_node.attributes['source_file'])

            inline_node.save()


def delete_old_attributes(apps, _):
    """Deletes the old attributes"""
    DbNode = apps.get_model('db', 'DbNode')

    with transaction.atomic():
        inline_type = 'process.calculation.calcfunction.CalcFunctionNode.'
        key_identifiers = ['namespace', 'function_namespace']  # If it has both it needs to be clean up
        inline_nodes = DbNode.objects.filter(node_type=inline_type, attributes__has_keys=key_identifiers)

        for inline_node in inline_nodes:
            inline_node.attributes.pop('namespace')
            inline_node.attributes.pop('source_code')
            inline_node.attributes.pop('source_file')
            inline_node.attributes.pop('first_line_source_code')
            inline_node.save()


#def delete_new_attributes(apps, _):
#"""Deletes the new attributes"""
#utils.del_object_from_repository(uuid, 'source_file')

#def create_old_attributes(apps, _):
#"""Re-creates the old attributes"""
#content_start = modifier.get_value_for_node(pk, 'function_starting_line_number')
#content_end = content_start + modifier.get_value_for_node(pk, 'function_number_of_lines')
#content0_text = utils.get_object_from_repository(uuid, 'source_file')
#content0_list = content0_text.splitlines()
#content_list = content0_list[content_start:content_end]
#content_text = "\n".join(content_list)


class Migration(migrations.Migration):
    """Migrate attributes from old InlineCalculation that have been transformed into CalcFunctions."""
    dependencies = [('db', '0045_dbgroup_extras')]
    operations = [
        # 1. We create the new attributes and copy the content
        migrations.RunPython(create_new_attributes, reverse_code=migrations.RunPython.noop),
        # 2. We delete the old attributes
        migrations.RunPython(delete_old_attributes, reverse_code=migrations.RunPython.noop),
        # 2. Finish migration
        upgrade_schema_version(REVISION, DOWN_REVISION),
    ]
