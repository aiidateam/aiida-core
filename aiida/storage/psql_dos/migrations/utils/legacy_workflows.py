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
"""Utilities for removing legacy workflows."""
import codecs
import json
import sys

import click
from sqlalchemy.sql import func, select, table

from aiida.cmdline.utils import echo


def json_serializer(obj):
    """JSON serializer for objects not serializable by default json code"""
    from datetime import date, datetime
    from uuid import UUID

    if isinstance(obj, UUID):
        return str(obj)

    if isinstance(obj, (datetime, date)):
        return obj.isoformat()

    raise TypeError(f'Type {type(obj)} not serializable')


def export_workflow_data(connection, profile):
    """Export existing legacy workflow data to a JSON file."""
    from tempfile import NamedTemporaryFile

    DbWorkflow = table('db_dbworkflow')
    DbWorkflowData = table('db_dbworkflowdata')
    DbWorkflowStep = table('db_dbworkflowstep')

    count_workflow = connection.execute(select(func.count()).select_from(DbWorkflow)).scalar()
    count_workflow_data = connection.execute(select(func.count()).select_from(DbWorkflowData)).scalar()
    count_workflow_step = connection.execute(select(func.count()).select_from(DbWorkflowStep)).scalar()

    # Nothing to do if all tables are empty
    if count_workflow == 0 and count_workflow_data == 0 and count_workflow_step == 0:
        return

    if not profile.is_test_profile:
        echo.echo('\n')
        echo.echo_warning('The legacy workflow tables contain data but will have to be dropped to continue.')
        echo.echo_warning('If you continue, the content will be dumped to a JSON file, before dropping the tables.')
        echo.echo_warning('This serves merely as a reference and cannot be used to restore the database.')
        echo.echo_warning('If you want a proper backup, make sure to dump the full database and backup your repository')
        if not click.confirm('Are you sure you want to continue', default=True):
            sys.exit(1)

    delete_on_close = profile.is_test_profile

    # pylint: disable=protected-access
    data = {
        'workflow': [dict(row._mapping) for row in connection.execute(select('*').select_from(DbWorkflow))],
        'workflow_data': [dict(row._mapping) for row in connection.execute(select('*').select_from(DbWorkflowData))],
        'workflow_step': [dict(row._mapping) for row in connection.execute(select('*').select_from(DbWorkflowStep))],
    }

    with NamedTemporaryFile(
        prefix='legacy-workflows', suffix='.json', dir='.', delete=delete_on_close, mode='wb'
    ) as handle:
        filename = handle.name
        json.dump(data, codecs.getwriter('utf-8')(handle), default=json_serializer)

    # If delete_on_close is False, we are running for the user and add additional message of file location
    if not delete_on_close:
        echo.echo_report(f'Exported workflow data to {filename}')
