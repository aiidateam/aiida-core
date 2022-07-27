# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Migration from v0.11 to v0.12, used by ``verdi archive migrate`` command.

This migration is necessary after the `core.` prefix was added to entry points shipped with `aiida-core`.
"""
from ..utils import update_metadata, verify_metadata_version  # pylint: disable=no-name-in-module

MAPPING_DATA = {
    'data.array.ArrayData.': 'data.core.array.ArrayData.',
    'data.array.bands.BandsData.': 'data.core.array.bands.BandsData.',
    'data.array.kpoints.KpointsData.': 'data.core.array.kpoints.KpointsData.',
    'data.array.projection.ProjectionData.': 'data.core.array.projection.ProjectionData.',
    'data.array.trajectory.TrajectoryData.': 'data.core.array.trajectory.TrajectoryData.',
    'data.array.xy.XyData.': 'data.core.array.xy.XyData.',
    'data.base.BaseData.': 'data.core.base.BaseData.',
    'data.bool.Bool.': 'data.core.bool.Bool.',
    'data.cif.CifData.': 'data.core.cif.CifData.',
    'data.code.Code.': 'data.core.code.Code.',
    'data.dict.Dict.': 'data.core.dict.Dict.',
    'data.float.Float.': 'data.core.float.Float.',
    'data.folder.FolderData.': 'data.core.folder.FolderData.',
    'data.int.Int.': 'data.core.int.Int.',
    'data.list.List.': 'data.core.list.List.',
    'data.numeric.NumericData.': 'data.core.numeric.NumericData.',
    'data.orbital.OrbitalData.': 'data.core.orbital.OrbitalData.',
    'data.remote.RemoteData.': 'data.core.remote.RemoteData.',
    'data.remote.stash.RemoteStashData.': 'data.core.remote.stash.RemoteStashData.',
    'data.remote.stash.folder.RemoteStashFolderData.': 'data.core.remote.stash.folder.RemoteStashFolderData.',
    'data.singlefile.SinglefileData.': 'data.core.singlefile.SinglefileData.',
    'data.str.Str.': 'data.core.str.Str.',
    'data.structure.StructureData.': 'data.core.structure.StructureData.',
    'data.upf.UpfData.': 'data.core.upf.UpfData.',
}

MAPPING_SCHEDULERS = {
    'direct': 'core.direct',
    'lsf': 'core.lsf',
    'pbspro': 'core.pbspro',
    'sge': 'core.sge',
    'slurm': 'core.slurm',
    'torque': 'core.torque',
}

MAPPING_CALCULATIONS = {
    'aiida.calculations:arithmetic.add': 'aiida.calculations:core.arithmetic.add',
    'aiida.calculations:templatereplacer': 'aiida.calculations:core.templatereplacer',
}

MAPPING_PARSERS = {
    'arithmetic.add': 'core.arithmetic.add',
    'templatereplacer.doubler': 'core.templatereplacer.doubler',
}

MAPPING_WORKFLOWS = {
    'aiida.workflows:arithmetic.add_multiply': 'aiida.workflows:core.arithmetic.add_multiply',
    'aiida.workflows:arithmetic.multiply_add': 'aiida.workflows:core.arithmetic.multiply_add',
}


def migrate_v11_to_v12(metadata: dict, data: dict) -> None:
    """Migration of export files from v0.11 to v0.12."""
    # pylint: disable=too-many-branches
    old_version = '0.11'
    new_version = '0.12'

    verify_metadata_version(metadata, old_version)
    update_metadata(metadata, new_version)

    # Migrate data entry point names
    for values in data.get('export_data', {}).get('Node', {}).values():
        if 'node_type' in values and values['node_type'].startswith('data.'):
            try:
                new_node_type = MAPPING_DATA[values['node_type']]
            except KeyError:
                pass
            else:
                values['node_type'] = new_node_type

        if 'process_type' in values and values['process_type'] and values['process_type'
                                                                          ].startswith('aiida.calculations:'):
            try:
                new_process_type = MAPPING_CALCULATIONS[values['process_type']]
            except KeyError:
                pass
            else:
                values['process_type'] = new_process_type

        if 'process_type' in values and values['process_type'] and values['process_type'
                                                                          ].startswith('aiida.workflows:'):
            try:
                new_process_type = MAPPING_WORKFLOWS[values['process_type']]
            except KeyError:
                pass
            else:
                values['process_type'] = new_process_type

    for attributes in data.get('export_data', {}).get('node_attributes', {}).values():
        if 'parser_name' in attributes:
            try:
                new_parser_name = MAPPING_PARSERS[attributes['parser_name']]
            except KeyError:
                pass
            else:
                attributes['parser_name'] = new_parser_name

    # Migrate scheduler entry point names
    for values in data.get('export_data', {}).get('Computer', {}).values():
        if 'scheduler_type' in values:
            try:
                new_scheduler_type = MAPPING_SCHEDULERS[values['scheduler_type']]
            except KeyError:
                pass
            else:
                values['scheduler_type'] = new_scheduler_type
