###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Implementation of Transfer CalcJob."""

import os

from aiida import orm
from aiida.common.datastructures import CalcInfo
from aiida.engine import CalcJob

from aiida.common.datastructures import StashMode


class StashCalculation(CalcJob):
    """Utility to stash files from a remote folder.

        inputs2 = {
                'metadata': {
                    'computer': Computer.collection.get(label=computer),
                    'description': 'Stash files from a remote folder',
                    'options': {
                        'resources': {'num_machines': 1},  # Define the required resources
                    },
                },
                'source_node': {
                    CalcJobNode,
                },
                'instructions': Dict({
                    'stash_mode': <>, 'target_basepath': <>, 'source_list': <>, 'dereference': <>, 'submission_script': <>
                })
    }
    """

    @classmethod
    def define(cls, spec):
        super().define(spec)

        spec.input_namespace(
            'parameters',
            valid_type=orm.CalcJobNode,
            dynamic=True,
            help='All the nodes that contain files referenced in the instructions.',
        )
        spec.input(
            'parameters',
            valid_type=orm.Dict,
            help='',
        )
        # The transfer just needs a computer, the code are resources are set here
        spec.inputs.pop('code', None)
        spec.inputs['metadata']['computer'].required = True
        spec.inputs['metadata']['options']['resources'].default = {
            'num_machines': 1,
            'num_mpiprocs_per_machine': 1,
        }

    def prepare_for_submission(self, folder):
        source_node = self.inputs.source_node
        parameters = self.inputs.parameters.get_dict()

        stash_mode = parameters.get('stash_mode')
        target_basepath = parameters.get('target_basepath', )
        source_list = parameters.get('source_list', [])
        dereference = parameters.get('dereference', False)
        submission_script = parameters.get('submission_script', None)

        calc_info = CalcInfo()
        if stash_mode != StashMode.CUSTUM_SCRIPT.value():
            calc_info.skip_submit = True
        
        calc_info.codes_info = []
        calc_info.retrieve_list = []

        # calc_info.local_copy_list = []
        calc_info.remote_copy_list = []
        # calc_info.remote_symlink_list = []

        # for source_label, source_relpath, target_relpath in local_files:
        #     source_node = source_nodes[source_label]
        #     retrieve_paths.append(target_relpath)
        #     calc_info.local_copy_list.append(
        #         (
        #             source_node.uuid,
        #             source_relpath,
        #             target_relpath,
        #         )
        #     )

        for source_label, source_relpath, target_relpath in remote_files:
            retrieve_paths.append(target_relpath)
            calc_info.remote_copy_list.append(
                (
                    source_node.computer.uuid,
                    os.path.join(source_node.get_remote_path(), source_relpath),
                    target_relpath,
                )
            )

        for source_label, source_relpath, target_relpath in symlink_files:
            source_node = source_nodes[source_label]
            retrieve_paths.append(target_relpath)
            calc_info.remote_symlink_list.append(
                (
                    source_node.computer.uuid,
                    os.path.join(source_node.get_remote_path(), source_relpath),
                    target_relpath,
                )
            )

        return calc_info
