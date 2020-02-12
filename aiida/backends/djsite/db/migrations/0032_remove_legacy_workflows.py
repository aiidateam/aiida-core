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
"""Remove legacy workflow."""

import sys
import click

# Remove when https://github.com/PyCQA/pylint/issues/1931 is fixed
# pylint: disable=no-name-in-module,import-error
from django.core import serializers
from django.db import migrations

from aiida.backends.djsite.db.migrations import upgrade_schema_version
from aiida.common import json
from aiida.cmdline.utils import echo
from aiida.manage import configuration

REVISION = '1.0.32'
DOWN_REVISION = '1.0.31'


def export_workflow_data(apps, _):
    """Export existing legacy workflow data to a JSON file."""
    from tempfile import NamedTemporaryFile

    DbWorkflow = apps.get_model('db', 'DbWorkflow')
    DbWorkflowData = apps.get_model('db', 'DbWorkflowData')
    DbWorkflowStep = apps.get_model('db', 'DbWorkflowStep')

    count_workflow = DbWorkflow.objects.count()
    count_workflow_data = DbWorkflowData.objects.count()
    count_workflow_step = DbWorkflowStep.objects.count()

    # Nothing to do if all tables are empty
    if count_workflow == 0 and count_workflow_data == 0 and count_workflow_step == 0:
        return

    if not configuration.PROFILE.is_test_profile:
        echo.echo('\n')
        echo.echo_warning('The legacy workflow tables contain data but will have to be dropped to continue.')
        echo.echo_warning('If you continue, the content will be dumped to a JSON file, before dropping the tables.')
        echo.echo_warning('This serves merely as a reference and cannot be used to restore the database.')
        echo.echo_warning('If you want a proper backup, make sure to dump the full database and backup your repository')
        if not click.confirm('Are you sure you want to continue', default=True):
            sys.exit(1)

    delete_on_close = configuration.PROFILE.is_test_profile

    data = {
        'workflow': serializers.serialize('json', DbWorkflow.objects.all()),
        'workflow_data': serializers.serialize('json', DbWorkflowData.objects.all()),
        'workflow_step': serializers.serialize('json', DbWorkflowStep.objects.all()),
    }

    with NamedTemporaryFile(
        prefix='legacy-workflows', suffix='.json', dir='.', delete=delete_on_close, mode='wb'
    ) as handle:
        filename = handle.name
        json.dump(data, handle)

    # If delete_on_close is False, we are running for the user and add additional message of file location
    if not delete_on_close:
        echo.echo_info('Exported workflow data to {}'.format(filename))


class Migration(migrations.Migration):
    """Remove legacy workflow."""

    dependencies = [
        ('db', '0031_remove_dbcomputer_enabled'),
    ]

    operations = [
        # Export existing data to a JSON file
        migrations.RunPython(export_workflow_data, reverse_code=migrations.RunPython.noop),
        migrations.RemoveField(
            model_name='dbworkflow',
            name='user',
        ),
        migrations.AlterUniqueTogether(
            name='dbworkflowdata',
            unique_together=set([]),
        ),
        migrations.RemoveField(
            model_name='dbworkflowdata',
            name='aiida_obj',
        ),
        migrations.RemoveField(
            model_name='dbworkflowdata',
            name='parent',
        ),
        migrations.AlterUniqueTogether(
            name='dbworkflowstep',
            unique_together=set([]),
        ),
        migrations.RemoveField(
            model_name='dbworkflowstep',
            name='calculations',
        ),
        migrations.RemoveField(
            model_name='dbworkflowstep',
            name='parent',
        ),
        migrations.RemoveField(
            model_name='dbworkflowstep',
            name='sub_workflows',
        ),
        migrations.RemoveField(
            model_name='dbworkflowstep',
            name='user',
        ),
        migrations.DeleteModel(name='DbWorkflow',),
        migrations.DeleteModel(name='DbWorkflowData',),
        migrations.DeleteModel(name='DbWorkflowStep',),
        upgrade_schema_version(REVISION, DOWN_REVISION)
    ]
