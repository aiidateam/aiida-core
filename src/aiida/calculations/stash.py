###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Implementation of StashCalculation."""

import json

from aiida import orm
from aiida.common import AIIDA_LOGGER
from aiida.common.datastructures import CalcInfo, CodeInfo, StashMode
from aiida.engine import CalcJob

EXEC_LOGGER = AIIDA_LOGGER.getChild('StashCalculation')


class StashCalculation(CalcJob):
    """
    Utility to stash files from a remote folder.

    An example of how the input should look like:

    .. code-block:: python

        inputs = {
            'metadata': {
                'computer': load_computer(label="localhost"),
                'options': {
                    'resources': {'num_machines': 1},
                    'stash': {
                        'stash_mode': StashMode.COPY.value,
                        'target_base': '/scratch/my_stashing/',
                        'source_list': ['aiida.in', '_aiidasubmit.sh'],
                    },
                },
            },
            'source_node': node_1,
        }

    Ideally one could use the same computer as the one of the `source_node`.
    However if you cannot access the stash storage from the same computer anymore
    but you have access to it from another computer, you can can specify the computer in `metadata.computer`.


    Only in case of `StashMode.SUBMIT_CUSTOM_CODE` mode, the `code` input is required.
    And the stashing is done by submitting a script to the computer specified in `metadata.computer`.
    For example:

    .. code-block:: python

        inputs = {
            'metadata': {
                'computer': load_computer(label="localhost"),
                'options': {
                    'resources': {'num_machines': 1},
                    'stash': {
                        'stash_mode': StashMode.SUBMIT_CUSTOM_CODE.value,
                        'target_base': '/scratch/my_stashing/',
                        'source_list': ['aiida.in', '_aiidasubmit.sh'],
                    },
                },
            },
            'source_node': <RemoteData_NODE>,
            'code': <MY_CODE>
        }
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @classmethod
    def define(cls, spec):
        super().define(spec)

        spec.input(
            'source_node',
            valid_type=orm.RemoteData,
            required=True,
            help='',
        )

        spec.inputs['metadata']['computer'].required = True
        spec.inputs['metadata']['options']['stash'].required = True
        spec.inputs['metadata']['options']['stash']['stash_mode'].required = True
        spec.inputs['metadata']['options']['stash']['target_base'].required = True
        spec.inputs['metadata']['options']['stash']['source_list'].required = True
        spec.inputs['metadata']['options']['resources'].default = {
            'num_machines': 1,
            'num_mpiprocs_per_machine': 1,
        }

        spec.inputs['metadata']['options']['input_filename'].default = 'aiida.in'
        spec.inputs['metadata']['options']['output_filename'].default = 'aiida.out'

    def prepare_for_submission(self, folder):
        if self.inputs.source_node.computer.uuid != self.inputs.metadata.computer.uuid:
            EXEC_LOGGER.warning(
                'YOUR SETTING MIGHT RESULT IN A SILENT FAILURE!'
                ' The computer of the source node and the computer of the calculation are strongly advised be the same.'
                ' However, it is not mandatory,'
                ' in order to support the case that original computer somehow is not usable, anymore.'
                ' E.g. the original computer was configured for ``core.torque``, but the HPC has move to SLURM,'
                ' so you had to create a new computer configured with ``core.slurm``,'
                " and you'll need a job submission to do this."
            )

        stash_mode = self.inputs.metadata.options.stash.get('stash_mode')

        calc_info = CalcInfo()

        if stash_mode == StashMode.SUBMIT_CUSTOM_CODE.value:
            with folder.open(self.options.input_filename, 'w', encoding='utf8') as handle:
                stash_dict = {
                    'source_path': self.inputs.source_node.get_remote_path(),
                    'source_list': self.inputs.metadata.options.stash.source_list,
                    'target_base': self.inputs.metadata.options.stash.target_base,
                }
                stash_json = json.dumps(stash_dict)
                handle.write(f'{stash_json}\n')

            code_info = CodeInfo()
            code_info.stdin_name = self.options.input_filename
            code_info.stdout_name = self.options.output_filename

            if 'code' in self.inputs:
                code_info.code_uuid = self.inputs.code.uuid
            else:
                raise ValueError(f"Input 'code' is required for `StashMode.{StashMode(stash_mode)}` mode.")

            calc_info.codes_info = [code_info]
            calc_info.retrieve_list = [self.options.output_filename]
            calc_info.local_copy_list = []
            calc_info.remote_copy_list = []
            calc_info.remote_symlink_list = []

            # The stashed node is going to be created by ``execmanager``, once the job is finished.

        else:
            if 'code' in self.inputs:
                raise ValueError(
                    f"Input 'code' cannot be used for `StashMode.{StashMode(stash_mode)}` mode."
                    ' This Stash mode is performed on the login node, '
                    'no submission is planned therefore no code is needed.'
                )

            calc_info.skip_submit = True

            calc_info.codes_info = []
            calc_info.retrieve_list = []
            calc_info.local_copy_list = []
            calc_info.remote_copy_list = []
            calc_info.remote_symlink_list = []

        return calc_info
