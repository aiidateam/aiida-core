###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
""""""

from aiida import orm
from aiida.common.datastructures import CalcInfo, CodeInfo, UnStashMode
from aiida.engine import CalcJob


class UnStashCalculation(CalcJob):
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
                        'unstash_mode': UnStashMode.OriginalPlace.value,
                        'unstash_mode': UnStashMode.NewFolderData.value,
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
            valid_type=(orm.RemoteStashCompressedData, orm.RemoteStashCustomData, orm.RemoteStashFolderData),
            required=True,
            help='',
        )

        spec.inputs['metadata']['options']['input_filename'].default = 'aiida.in'
        spec.inputs['metadata']['options']['output_filename'].default = 'aiida.out'
        # Code is irrelevant for this calculation.
        spec.inputs.pop('code', None)

        # Ideally one could use the same computer as the one of the `source_node`.
        # However, if another computer has access to the directory, we don't want to restrict.`
        spec.inputs['metadata']['computer'].required = True
        spec.inputs['metadata']['options']['resources'].default = {
            'num_machines': 1,
            'num_mpiprocs_per_machine': 1,
        }

    def prepare_for_submission(self, folder):
        source_node = self.inputs.get('source_node')
        unstash_mode = self.inputs.metadata.options.stash.get('unstash_mode')


        calc_info = CalcInfo()

        if isinstance(source_node, (orm.RemoteStashCompressedData, orm.RemoteStashFolderData)):
            calc_info.skip_submit = True

            calc_info.codes_info = []
            calc_info.retrieve_list = []
            calc_info.local_copy_list = []
            calc_info.remote_copy_list = []
            calc_info.remote_symlink_list = []

        elif isinstance(source_node, orm.RemoteStashCustomData):
            custom_command = self.inputs.metadata.options.stash.get('custom_command')

            if custom_command is None:
                raise ValueError("Input 'custom_command' is required for `StashMode.CUSTOM_SCRIPT` mode.")
            
            if unstash_mode == UnStashMode.OriginalPlace.value:
                src_of_the_src= orm.load_node(source_node.source_uuid)
                working_directory = src_of_the_src.get_remote_path()  # type: ignore[union-attr]
            elif unstash_mode == UnStashMode.NewFolderData.value:
                # TODO:
                # Execmanager should make REmoteDAta
                # Generate a path, so the submitted job can put the data directly there. 
                # Give that path to execmanager to generate and save a RemoteData node.
                


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



        return calc_info
