###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Implementation of UnstashCalculation."""

import json
from pathlib import Path

from aiida import orm
from aiida.common import AIIDA_LOGGER
from aiida.common.datastructures import CalcInfo, CodeInfo, UnstashTargetMode
from aiida.engine import CalcJob

from .stash import StashCalculation

EXEC_LOGGER = AIIDA_LOGGER.getChild('UnstashCalculation')


class UnstashCalculation(CalcJob):
    """
    Utility to unstash files from a remote folder.

    An example of how the input should look like:

    .. code-block:: python

        inputs = {
            'metadata': {
                'computer': Computer.collection.get(label="localhost"),
                'options': {
                    'resources': {'num_machines': 1},
                    'unstash': {
                        'unstash_target_mode': UnstashTargetMode.NewNode.value,
                        'source_list': ['aiida.in', '_aiidasubmit.sh'],     # also accepts ['*']
                    },
                },
            },
            'source_node': <RemoteStashData>,
            'code': <MY_CODE>      # only in case of `type(source_node)==RemoteStashCustomData`
        }
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @classmethod
    def define(cls, spec):
        super().define(spec)

        spec.input(
            'source_node',
            valid_type=orm.RemoteStashData,
            required=True,
            help='',
        )

        spec.inputs['metadata']['computer'].required = True
        spec.inputs['metadata']['options']['unstash'].required = True
        spec.inputs['metadata']['options']['unstash']['unstash_target_mode'].required = True
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
        source_node = self.inputs.get('source_node')
        unstash_target_mode = self.inputs.metadata.options.unstash.get('unstash_target_mode')

        calc_info = CalcInfo()

        if isinstance(source_node, orm.RemoteStashCustomData):
            if unstash_target_mode == UnstashTargetMode.OriginalPlace.value:

                def traverse(node_):
                    for link in node_.base.links.get_incoming():
                        if (isinstance(link.node, CalcJob) and not isinstance(link.node, StashCalculation)) or (
                            isinstance(link.node, orm.RemoteData)
                        ):
                            return link.node
                        return traverse(link.node)
                    return None

                stashed_calculation_node = traverse(source_node)

                if not stashed_calculation_node:
                    raise ValueError(
                        'Your stash node is not connected to any calcjob node, cannot find the source path.'
                    )

                target_path = stashed_calculation_node.get_remote_path()
            else:  # UnstashTargetMode.NewRemoteData.value
                computer = self.inputs.metadata.get('computer')
                with computer.get_transport() as transport:
                    remote_user = transport.whoami()
                remote_working_directory = computer.get_workdir().format(username=remote_user)

                # The following line is set at calcjob::presubmit, but we need it here
                calc_info_uuid = str(self.node.uuid)

                # This is normally done in execmanager::upload_calculation,
                # however unfortunatly is not modular and I had to copy-paste the logic here
                target_path = Path(remote_working_directory).joinpath(
                    calc_info_uuid[:2], calc_info_uuid[2:4], calc_info_uuid[4:]
                )

            with folder.open(self.options.input_filename, 'w', encoding='utf8') as handle:
                stash_dict = {
                    'source_path': self.inputs.source_node.target_basepath,
                    'source_list': self.inputs.metadata.options.unstash.get('source_list'),
                    'target_base': str(target_path),
                }
                stash_json = json.dumps(stash_dict)
                handle.write(f'{stash_json}\n')

            code_info = CodeInfo()
            code_info.stdin_name = self.options.input_filename
            code_info.stdout_name = self.options.output_filename

            if 'code' in self.inputs:
                code_info.code_uuid = self.inputs.code.uuid
            else:
                raise ValueError(
                    f"Input 'code' is required for `UnstashTargetMode.{UnstashTargetMode(unstash_target_mode)}` mode."
                )

            calc_info.codes_info = [code_info]
            calc_info.retrieve_list = [self.options.output_filename]
            calc_info.local_copy_list = []
            calc_info.remote_copy_list = []
            calc_info.remote_symlink_list = []

        else:
            if 'code' in self.inputs:
                raise ValueError(
                    f"Input 'code' cannot be used for `UnstashTargetMode.{UnstashTargetMode(unstash_target_mode)}`"
                    ' mode. This UnStash mode is performed on the login node, '
                    'no submission is planned therefore no code is needed.'
                )

            calc_info.skip_submit = True

            calc_info.codes_info = []
            calc_info.retrieve_list = []
            calc_info.local_copy_list = []
            calc_info.remote_copy_list = []
            calc_info.remote_symlink_list = []

        return calc_info
