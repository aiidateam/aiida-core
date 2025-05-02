###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Implementation of StashCalculation."""

from aiida import orm
from aiida.common.datastructures import CalcInfo, CodeInfo, StashMode
from aiida.engine import CalcJob


class StashCalculation(CalcJob):
    """
    Utility to stash files from a remote folder.

    An example of how the input should look like:

    .. code-block:: python

        inputs = {
            'metadata': {
                'computer': Computer.collection.get(label="localhost"),
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

    Or in case of a custom script, 'source_list' and 'target_base' are stored
    as a bash array and bash variable, respectively.
    The 'custom_command' could be a bash command that uses these variables,
    Before executing 'custom_command', working directory is set to the one of 'source_node'.
    For example:

    .. code-block:: python

        inputs = {
            'metadata': {
                'computer': Computer.collection.get(label="localhost"),
                'options': {
                    'resources': {'num_machines': 1},
                    'stash': {
                        'stash_mode': StashMode.CUSTOM_SCRIPT.value,
                    },
                },
            },
            'source_node': node_1,
            'custom_command': 'rsync -av aiida.in _aiidasubmit.sh /scratch/my_stashing/',
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

        # Code is irrelevant for this calculation.
        spec.inputs.pop('code', None)

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
        source_node = self.inputs.get('source_node')
        stash_mode = self.inputs.metadata.options.stash.get('stash_mode')

        calc_info = CalcInfo()

        if stash_mode == StashMode.CUSTOM_SCRIPT.value:
            custom_command = self.inputs.metadata.options.stash.get('custom_command')

            if custom_command is None:
                raise ValueError("Input 'custom_command' is required for `StashMode.CUSTOM_SCRIPT` mode.")

            working_directory = source_node.get_remote_path()  # type: ignore[union-attr]
            change_dir = f'cd {working_directory}\n'

            with folder.open(self.options.input_filename, 'w', encoding='utf8') as handle:
                the_scripts = change_dir + '\n' + custom_command
                handle.write(the_scripts)

            code_info = CodeInfo()
            code_info.stdin_name = self.options.input_filename
            code_info.stdout_name = self.options.output_filename

            calc_info.codes_info = [code_info]
            calc_info.retrieve_list = [self.options.output_filename]
            calc_info.local_copy_list = []
            calc_info.remote_copy_list = []
            calc_info.remote_symlink_list = []

            # The stashed node is going to be created by ``execmanager``, once the job is finished.

        else:
            calc_info.skip_submit = True

            calc_info.codes_info = []
            calc_info.retrieve_list = []
            calc_info.local_copy_list = []
            calc_info.remote_copy_list = []
            calc_info.remote_symlink_list = []

        return calc_info
