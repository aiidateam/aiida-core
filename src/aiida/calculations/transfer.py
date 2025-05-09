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


def validate_instructions(instructions, _):
    """Check that the instructions dict contains the necessary keywords"""
    instructions_dict = instructions.get_dict()
    retrieve_files = instructions_dict.get('retrieve_files', None)

    if retrieve_files is None:
        errmsg = (
            '\n\n'
            'no indication of what to do in the instruction node:\n'
            f' > {instructions.uuid}\n'
            '(to store the files in the repository set retrieve_files=True,\n'
            'to copy them to the specified folder on the remote computer,\n'
            'set it to False)\n'
        )
        return errmsg

    if not isinstance(retrieve_files, bool):
        errmsg = (
            'entry for retrieve files inside of instruction node:\n'
            f' > {instructions.uuid}\n'
            'must be either True or False; instead, it is:\n'
            f' > {retrieve_files}\n'
        )
        return errmsg

    local_files = instructions_dict.get('local_files', None)
    remote_files = instructions_dict.get('remote_files', None)
    symlink_files = instructions_dict.get('symlink_files', None)

    if not any([local_files, remote_files, symlink_files]):
        errmsg = (
            'no indication of which files to copy were found in the instruction node:\n'
            f' > {instructions.uuid}\n'
            'Please include at least one of `local_files`, `remote_files`, or `symlink_files`.\n'
            'These should be lists containing 3-tuples with the following format:\n'
            '    (source_node_key, source_relpath, target_relpath)\n'
        )
        return errmsg


def validate_transfer_inputs(inputs, _ctx):
    """Check that the instructions dict and the source nodes are consistent"""
    source_nodes = inputs['source_nodes']
    instructions = inputs['instructions']
    computer = inputs['metadata']['computer']

    instructions_dict = instructions.get_dict()
    local_files = instructions_dict.get('local_files', [])
    remote_files = instructions_dict.get('remote_files', [])
    symlink_files = instructions_dict.get('symlink_files', [])

    source_nodes_provided = set(source_nodes.keys())
    source_nodes_required = set()
    error_message_list = []

    for node_label, node_object in source_nodes.items():
        if isinstance(node_object, orm.RemoteData):
            if computer.label != node_object.computer.label:
                error_message = (
                    f' > remote node `{node_label}` points to computer `{node_object.computer}`, '
                    f'not the one being used (`{computer}`)'
                )
                error_message_list.append(error_message)

    for source_label, _, _ in local_files:
        source_nodes_required.add(source_label)
        source_node = source_nodes.get(source_label, None)
        error_message = check_node_type('local_files', source_label, source_node, orm.FolderData)
        if error_message:
            error_message_list.append(error_message)

    for source_label, _, _ in remote_files:
        source_nodes_required.add(source_label)
        source_node = source_nodes.get(source_label, None)
        error_message = check_node_type('remote_files', source_label, source_node, orm.RemoteData)
        if error_message:
            error_message_list.append(error_message)

    for source_label, _, _ in symlink_files:
        source_nodes_required.add(source_label)
        source_node = source_nodes.get(source_label, None)
        error_message = check_node_type('symlink_files', source_label, source_node, orm.RemoteData)
        if error_message:
            error_message_list.append(error_message)

    unrequired_nodes = source_nodes_provided.difference(source_nodes_required)
    for node_label in unrequired_nodes:
        error_message = f' > node `{node_label}` provided as inputs is not being used'
        error_message_list.append(error_message)

    if len(error_message_list) > 0:
        error_message = '\n\n'
        for error_add in error_message_list:
            error_message = error_message + error_add + '\n'
        return error_message


def check_node_type(list_name, node_label, node_object, node_type):
    """Common utility function to check the type of a node"""
    if node_object is None:
        return f' > node `{node_label}` requested on list `{list_name}` not found among inputs'

    if not isinstance(node_object, node_type):
        target_class = node_type.class_node_type
        return f' > node `{node_label}`, requested on list `{list_name}` should be of type `{target_class}`'

    return None


class TransferCalculation(CalcJob):
    """Utility to copy files from different FolderData and RemoteData nodes into a single place.

    The final destination for these files can be either the local repository (by creating a
    new FolderData node to store them) or in the remote computer (by leaving the files in a
    new remote folder saved in a RemoteData node).

    Only files from the local computer and from remote folders in the same external computer
    can be moved at the same time with a single instance of this CalcJob.

    The user needs to provide three inputs:

        * ``instructions``: a dict node specifying which files to copy from which nodes.
        * ``source_nodes``: a dict of nodes, each with a unique identifier label as its key.
        * ``metadata.computer``: the computer that contains the remote files and will contain
          the final RemoteData node.

    The ``instructions`` dict must have the ``retrieve_files`` flag. The CalcJob will create a
    new folder in the remote machine (``RemoteData``) and put all the files there and will either:

        (1) leave them there (``retrieve_files = False``) or ...
        (2) retrieve all the files and store them locally in a ``FolderData``  (``retrieve_files = True``)

    The `instructions` dict must also contain at least one list with specifications of which files
    to copy and from where. All these lists take tuples of 3 that have the following format:

    .. code-block:: python

        ( source_node_key, path_to_file_in_source, path_to_file_in_target)

    where the ``source_node_key`` has to be the respective one used when providing the node in the
    ``source_nodes`` input nodes dictionary.


    The two main lists to include are ``local_files`` (for files to be taken from FolderData nodes)
    and ``remote_files`` (for files to be taken from RemoteData nodes). Alternatively, files inside
    of RemoteData nodes can instead be put in the ``symlink_files`` list: the only difference is that
    files from the first list will be fully copied in the target RemoteData folder, whereas for the
    files in second list only a symlink to the original file will be created there. This will only
    affect the content of the final RemoteData target folder, but in both cases the full file will
    be copied back in the local target FolderData (if ``retrieve_files = True``).
    """

    @classmethod
    def define(cls, spec):
        super().define(spec)

        spec.input(
            'instructions',
            valid_type=orm.Dict,
            help='A dictionary containing the `retrieve_files` flag and at least one of the file lists:'
            '`local_files`, `remote_files` and/or `symlink_files`.',
            validator=validate_instructions,
        )
        spec.input_namespace(
            'source_nodes',
            valid_type=(orm.FolderData, orm.RemoteData),
            dynamic=True,
            help='All the nodes that contain files referenced in the instructions.',
        )

        # The transfer just needs a computer, the code and resources are set here
        spec.inputs.pop('code', None)
        spec.inputs['metadata']['computer'].required = True
        spec.inputs['metadata']['options']['resources'].default = {
            'num_machines': 1,
            'num_mpiprocs_per_machine': 1,
        }

        spec.inputs.validator = validate_transfer_inputs

    def prepare_for_submission(self, folder):
        source_nodes = self.inputs.source_nodes
        instructions = self.inputs.instructions.get_dict()

        local_files = instructions.get('local_files', [])
        remote_files = instructions.get('remote_files', [])
        symlink_files = instructions.get('symlink_files', [])
        retrieve_files = instructions.get('retrieve_files')

        calc_info = CalcInfo()
        calc_info.skip_submit = True
        calc_info.codes_info = []
        calc_info.local_copy_list = []
        calc_info.remote_copy_list = []
        calc_info.remote_symlink_list = []
        retrieve_paths = []

        for source_label, source_relpath, target_relpath in local_files:
            source_node = source_nodes[source_label]
            retrieve_paths.append(target_relpath)
            calc_info.local_copy_list.append(
                (
                    source_node.uuid,
                    source_relpath,
                    target_relpath,
                )
            )

        for source_label, source_relpath, target_relpath in remote_files:
            source_node = source_nodes[source_label]
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

        if retrieve_files:
            calc_info.retrieve_list = retrieve_paths
        else:
            calc_info.retrieve_list = []

        return calc_info
