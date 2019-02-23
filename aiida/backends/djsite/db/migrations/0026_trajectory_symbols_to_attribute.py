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
# pylint: disable=no-member,no-name-in-module,import-error
from django.db import migrations

from aiida.backends.djsite.db.migrations import upgrade_schema_version
from . import ModelModifierV0025

REVISION = '1.0.26'
DOWN_REVISION = '1.0.25'


def get_numpy_array_absolute_path(uuid, name):
    """Get the absolute path of a numpy array with the given name in the repository of the node with the given uuid.

    :param uuid: the UUID of the node
    :param name: the name of the numpy array
    :return: the absolute path of the numpy array file
    """
    import os
    from aiida.common.utils import get_repository_folder
    repo_dirpath = get_repository_folder('repository')
    node_dirpath = os.path.join(repo_dirpath, 'node', uuid[:2], uuid[2:4], uuid[4:], 'path')
    filepath = os.path.join(node_dirpath, name + '.npy')
    return filepath


def get_numpy_array_from_disk(uuid, name):
    """Get a numpy array with the given name stored on the file system in the repository for the node with the given UUID."""
    filepath = get_numpy_array_absolute_path(uuid, name)
    return numpy.load_fromtxt(filepath)  # something like this


def create_trajectory_symbols_attribute(apps, _):
    """Create the symbols attribute from the repository array for all `TrajectoryData` nodes."""
    DbAttribute = apps.get_model('db', 'DbAttribute')

    modifier = ModelModifierV0025(DbAttribute)

    DbNode = apps.get_model('db', 'DbNode')
    trajectories = DbNode.objects.filter(type='node.data.array.trajectory.TrajectoryData.').values_list('id', 'uuid')
    for pk, uuid in trajectories:
        symbols = get_numpy_array_from_disk(uuid, 'symbols').tolist()
        modifier.set_value_for_node(DbNode.objects.get(pk=pk), 'symbols', symbols)


def delete_trajectory_symbols_attribute(apps, _):
    """Delete the symbols attribute for all `TrajectoryData` nodes."""
    DbAttribute = apps.get_model('db', 'DbAttribute')

    modifier = ModelModifierV0025(DbAttribute)

    DbNode = apps.get_model('db', 'DbNode')
    trajectories_pk = DbNode.objects.filter(type='node.data.array.trajectory.TrajectoryData.').values_list(
        'id', flat=True)
    for t_pk in trajectories_pk:
        modifier.del_value_for_node(DbNode.objects.get(pk=t_pk), 'symbols')


class Migration(migrations.Migration):
    """Storing symbols in TrajectoryData nodes as attributes, while keeping numpy arrays.
    TrajectoryData symbols arrays are deleted in the next migration.
    We split the migration into two because every migration is wrapped in an atomic transaction and we want to avoid
    to delete the data while it is written in the database"""

    dependencies = [
        ('db', '0025_move_data_within_node_module'),
    ]

    operations = [
        migrations.RunPython(create_trajectory_symbols_attribute, reverse_code=delete_trajectory_symbols_attribute),
        upgrade_schema_version(REVISION, DOWN_REVISION)
    ]
