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
from aiida.common.datastructures import CalcInfo
from aiida.engine import CalcJob


class StashCalculation(CalcJob):
    """
    Utility to stash files/folders from `RemoteData`, `SinglefileData`, or `FolderData`.

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

    def prepare_for_submission(self, folder):
        calc_info = CalcInfo()
        calc_info.skip_submit = True

        calc_info.codes_info = []
        calc_info.retrieve_list = []
        calc_info.local_copy_list = []
        calc_info.remote_copy_list = []
        calc_info.remote_symlink_list = []

        return calc_info
