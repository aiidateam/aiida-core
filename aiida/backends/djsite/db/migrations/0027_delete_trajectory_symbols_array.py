# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
# pylint: disable=invalid-name,too-few-public-methods
"""Data migration for `TrajectoryData` nodes where symbol lists are moved from repository array to attribute.

This process has to be done in two separate consecutive migrations to prevent data loss in between.
"""
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
from __future__ import absolute_import

# Remove when https://github.com/PyCQA/pylint/issues/1931 is fixed
# pylint: disable=no-name-in-module,import-error
from django.db import migrations

from aiida.backends.djsite.db.migrations import upgrade_schema_version
from . import ModelModifierV0025

REVISION = '1.0.27'
DOWN_REVISION = '1.0.26'


def get_numpy_array_absolute_path(uuid, name):
    """Get the absolute path of a numpy array with the given name in the repository of the node with the given uuid.

    :param uuid: the UUID of the node
    :param name: the name of the numpy array
    :return: the absolute path of the numpy array file
    """
    from aiida.common.utils import get_repository_folder
    repo_dirpath = get_repository_folder('repository')
    node_dirpath = os.path.join(repo_dirpath, 'node', uuid[:2], uuid[2:4], uuid[4:], 'path')
    filepath = os.path.join(node_dirpath, name + '.npy')
    return filepath


def delete_numpy_array_from_repository(uuid, name):
    filepath = get_numpy_array_absolute_path(uuid, name)
    os.delete(...)


def delete_trajectory_symbols_array(apps, _):
    """Delete the symbols array from all `TrajectoryData` nodes."""
    DbAttribute = apps.get_model('db', 'DbAttribute')

    modifier = ModelModifierV0025(DbAttribute)

    DbNode = apps.get_model('db', 'DbNode')
    trajectories = DbNode.objects.filter(type='node.data.array.trajectory.TrajectoryData.').values_list('id', 'uuid')
    for pk, uuid in trajectories:
        modifier.del_value_for_node(DbNode.objects.get(pk=pk), 'array|symbols')
        delete_numpy_array_from_repository(uuid, 'symbols')


def create_trajectory_symbols_array(apps, _):
    """Create the symbols array for all `TrajectoryData` nodes."""
    import numpy
    import tempfile
    from aiida.orm import load_node

    DbAttribute = apps.get_model('db', 'DbAttribute')

    modifier = ModelModifierV0025(DbAttribute)

    DbNode = apps.get_model('db', 'DbNode')
    trajectories_pk = DbNode.objects.filter(type='node.data.array.trajectory.TrajectoryData.').values_list(
        'id', flat=True)
    for t_pk in trajectories_pk:
        trajectory = load_node(t_pk)
        symbols = numpy.array(trajectory.get_attribute('symbols'))
        # Save the .npy file (using set_array raises ModificationNotAllowed error)
        with tempfile.NamedTemporaryFile() as handle:
            numpy.save(handle, symbols)
            handle.flush()
            handle.seek(0)
            trajectory.put_object_from_filelike(handle, 'symbols.npy')
        modifier.set_value_for_node(DbNode.objects.get(pk=trajectory.pk), 'array|symbols', list(symbols.shape))


class Migration(migrations.Migration):
    """Deleting duplicated information stored in TrajectoryData symbols numpy arrays"""

    dependencies = [
        ('db', '0026_trajectory_symbols_to_attribute'),
    ]

    operations = [
        migrations.RunPython(delete_trajectory_symbols_array, reverse_code=create_trajectory_symbols_array),
        upgrade_schema_version(REVISION, DOWN_REVISION)
    ]
