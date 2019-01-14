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


def delete_trajectory_symbols_array(apps, _):
    """Delete the symbols array from all `TrajectoryData` nodes."""
    from aiida.orm import load_node

    DbAttribute = apps.get_model('db', 'DbAttribute')

    modifier = ModelModifierV0025(DbAttribute)

    DbNode = apps.get_model('db', 'DbNode')
    trajectories_pk = DbNode.objects.filter(type='node.data.array.trajectory.TrajectoryData.').values_list(
        'id', flat=True)
    for t_pk in trajectories_pk:
        trajectory = load_node(t_pk)
        modifier.del_value_for_node(DbNode.objects.get(pk=trajectory.pk), 'array|symbols')
        # Remove the .npy file (using delete_array raises ModificationNotAllowed error)
        trajectory._get_folder_pathsubfolder.remove_path('symbols.npy')  # pylint: disable=protected-access


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
        symbols = numpy.array(trajectory.get_attr('symbols'))
        # Save the .npy file (using set_array raises ModificationNotAllowed error)
        with tempfile.NamedTemporaryFile() as _file:
            numpy.save(_file, symbols)
            _file.flush()
            trajectory._get_folder_pathsubfolder.insert_path(_file.name, 'symbols.npy')  # pylint: disable=protected-access
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
