###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Functions for dumping of workchains and calcjobs."""

from __future__ import annotations

import textwrap
from pathlib import Path

import yaml

from aiida.cmdline.utils import echo
from aiida.common import LinkType
from aiida.common.exceptions import NotExistentAttributeError
from aiida.common.folders import Folder
from aiida.engine.daemon.execmanager import upload_calculation
from aiida.engine.processes.calcjobs import CalcJob
from aiida.engine.utils import instantiate_process
from aiida.manage import get_manager
from aiida.orm import (
    CalcFunctionNode,
    CalcJobNode,
    FolderData,
    ProcessNode,
    SinglefileData,
    WorkChainNode,
    WorkFunctionNode,
)
from aiida.orm.utils import LinkTriple
from aiida.transports.plugins.local import LocalTransport


class ProcessNodeYamlDumper:
    """Utility class to dump selected `ProcessNode` properties and, optionally, attributes and extras to yaml."""

    NODE_PROPERTIES = [
        'label',
        'description',
        'pk',
        'uuid',
        'ctime',
        'mtime',
        'node_type',
        'process_type',
        'is_finished_ok',
    ]

    USER_PROPERTIES = ('first_name', 'last_name', 'email', 'institution')

    COMPUTER_PROPERTIES = ('label', 'hostname', 'scheduler_type', 'transport_type')

    def __init__(self, include_attributes: bool = True, include_extras: bool = True):
        self.include_attributes = include_attributes
        self.include_extras = include_extras

    def dump_yaml(
        self,
        process_node: ProcessNode,
        output_path: Path,
        output_filename: str = '.aiida_node_metadata.yaml',
    ) -> None:
        """Dump the selected `ProcessNode` properties, attributes, and extras to a yaml file.

        :param process_node: The ProcessNode to dump.
        :param output_path: The path to the directory where the yaml file will be saved.
        :param output_filename: The name of the output yaml file. Defaults to `.aiida_node_metadata.yaml`.
        :return: None
        """

        node_dict = {}
        metadata_dict = {}

        # Add actual node `@property`s to dictionary
        for metadata_property in self.NODE_PROPERTIES:
            metadata_dict[metadata_property] = getattr(process_node, metadata_property)

        node_dict['Node data'] = metadata_dict

        # Add user data
        try:
            node_dbuser = process_node.user
            user_dict = {}
            for user_property in self.USER_PROPERTIES:
                user_dict[user_property] = getattr(node_dbuser, user_property)
            node_dict['User data'] = user_dict
        except AttributeError:
            pass

        # Add computer data
        try:
            node_dbcomputer = process_node.computer
            computer_dict = {}
            for computer_property in self.COMPUTER_PROPERTIES:
                computer_dict[computer_property] = getattr(node_dbcomputer, computer_property)
            node_dict['Computer data'] = computer_dict
        except AttributeError:
            pass

        # Add node attributes
        if self.include_attributes is True:
            node_attributes = process_node.base.attributes.all
            node_dict['Node attributes'] = node_attributes

        # Add node extras
        if self.include_extras is True:
            node_extras = process_node.base.extras.all
            if node_extras:
                node_dict['Node extras'] = node_extras

        # Dump to file
        output_file = output_path.resolve() / output_filename
        with open(output_file, 'w') as handle:
            yaml.dump(node_dict, handle, sort_keys=False)


# Utility functions
def make_dump_readme(process_node: ProcessNode, output_path: Path):
    """Generate README file in main dumping directory.

    :param process_node: CalcJob or WorkChain Node.
    :type process_node: ProcessNode
    :param output_path: Output path for dumping.
    :type output_path: Path

    """
    _readme_string = textwrap.dedent(
        f"""\
    This directory contains the files involved in the simulation/workflow `{process_node.process_label} <{process_node.pk}>` run with AiiDA.

    Child simulations/workflows (also called `CalcJob`s and `WorkChain`s in AiiDA jargon) run by the parent workflow are
    contained in the directory tree as sub-folders and are sorted by their creation time. The directory tree thus
    mirrors the logical execution of the workflow, which can also be queried by running `verdi process status
    {process_node.pk}` on the command line.

    By default, input and output files of each simulation can be found in the corresponding "raw_inputs" and
    "raw_outputs" directories (the former also contains the hidden ".aiida" folder with machine-readable job execution
    settings). Additional input files (depending on the type of calculation) are placed in the "node_inputs".

    When using the `--use-presubmit` command line option, the folder created for each individual simulation should, in
    principle, allow for direct resubmission, as it mirrors the (remote) folder that was created by AiiDA to execute the
    job. However, this option requires the relevant AiiDA plugin to be installed, so it is disabled by default. Also
    note that intermediate files might be missing, so for a multi-step workflow, each step would still have to be run
    separately.

    Lastly, every folder also contains a hidden, human-readable `.aiida_node_metadata.yaml` file with the relevant AiiDA
    node data for further inspection."""  # noqa: E501
    )

    # TODO: Add outputs of `verdi process (status|report|show?)`

    with open(output_path / 'README', 'w') as handle:
        handle.write(_readme_string)


def generate_default_dump_path(process_node: WorkChainNode | CalcJobNode) -> Path:
    """Simple helper function to generate the default parent-dumping directory if none given.

    This function is not called for the sub-calls of `calcjob_dump` or during the recursive `workchain_dump` as it just
    creates the default parent folder for the dumping, if no name is given.

    :param process_node: The `ProcessNode` for which the directory is created.
    :type process_node: WorkChainNode | CalcJobNode
    :return: The created parent dump path.
    :rtype: Path
    """

    try:
        return Path(f'dump-{process_node.process_label}-{process_node.pk}')
    except AttributeError:
        # ? This case came up during testing, not sure how relevant it actually is
        return Path(f'dump-{process_node.process_type}-{process_node.pk}')


# ? Could move code from `generate_calcjob_node_io` here to normal function
def attach_files_to_calcjob():
    pass


# ? Could move this to `cmdline/utils`
def validate_make_dump_path(
    path: Path = Path(),
    overwrite: bool = False,
) -> Path:
    """
    Create default dumping directory for a given process node and return it as absolute path.

    :param path: The base path for the dump. Defaults to the current directory.
    :type path: Path
    :return: The created dump path.
    :rtype: Path
    """
    import shutil

    output_path = path.resolve()

    # ? Use of `echo.echo_` only when running via `verdi`? -> I only see it used in the `cmd_` files.
    if str(path) == '.' and overwrite:
        echo.echo_critical('Path not set, defaults to CWD. Will not delete here for safety.')
        return output_path

    if output_path.is_dir() and any(output_path.iterdir()):
        if overwrite:
            # ? This might be a bit dangerous -> Check for it not being CWD enough?
            # ? Added check for README in folder to decrease chances of deleting some other path
            if (output_path / 'README').is_file():  # Also check for presence of README for safety
                echo.echo_report(f'Overwrite set to true, will overwrite directory `{output_path}`.')
                shutil.rmtree(output_path)
            else:
                echo.echo_critical(f'Something went wrong. Manually remove existing `{output_path}` and dump again.')
                # echo.echo_critical(f'No README present in "{output_path}" Manually remove and dump again.')
        else:
            echo.echo_critical(f'Path `{output_path}` already exists and overwrite set to False.')

    output_path.mkdir(parents=True, exist_ok=False)

    return output_path


def generate_node_input_label(index: int, link_triple: LinkTriple) -> str:
    """Small helper function to generate the directory label for node inputs."""
    node = link_triple.node
    link_label = link_triple.link_label

    # Generate directories with naming scheme akin to `verdi process status`
    if link_label != 'CALL' and not link_label.startswith('iteration_'):
        node_label = f'{index:02d}-{link_label}'
    else:
        node_label = f'{index:02d}'

    try:
        process_label = node.process_label
        if process_label is not None:
            node_label += f'-{process_label}'

    except AttributeError:
        process_type = node.process_type
        if process_type is not None:
            node_label += f'-{process_type}'

    # ? Add pk also to the sub-steps or only the parent dumping directory?
    # node_label += f'-{node.pk}'

    return node_label


def calcjob_dump(
    calcjob_node: CalcJobNode,
    output_path: Path = Path(),
    no_node_inputs: bool = False,
    use_presubmit: bool = False,
    node_dumper: ProcessNodeYamlDumper | None = None,
    overwrite: bool = True,
) -> bool:
    """
    Dump the contents of a CalcJobNode to a specified output path.

    :param calcjob_node: The CalcJobNode to be dumped.
    :param output_path: The path where the dumped contents will be stored.
    :param no_node_inputs: If True, do not dump the inputs of the CalcJobNode.
    :param use_presubmit: If True, use the `prepare_for_submission` method to prepare the calculation for
        submission. If False, use the retrieved outputs and raw inputs.
    :return: None
    """

    output_path = validate_make_dump_path(path=output_path, overwrite=overwrite)

    if not use_presubmit:
        # ? Outputs obtained via retrieved and should not be present when using `prepare_for_submission` as it puts the
        # ? calculation in a state to be submitted ?!
        calcjob_node.base.repository.copy_tree(output_path / Path('raw_inputs'))
        try:
            calcjob_node.outputs.retrieved.copy_tree(output_path / Path('raw_outputs'))

        # Might not have an output with link label `retrieved`
        except NotExistentAttributeError:
            pass

        if not no_node_inputs:
            calcjob_node_inputs_dump(calcjob_node=calcjob_node, output_path=output_path)

    else:
        try:
            calcjob_presubmit_dump(calcjob_node=calcjob_node, output_path=output_path)
        except ValueError:
            # raise
            echo.echo_error(
                'Error when trying to get a restart-builder. Do you have the relevant aiida-plugin installed?'
            )
            return False

    # This will eventually be replaced once pydantic backend PR merged
    if node_dumper is None:
        node_dumper = ProcessNodeYamlDumper()
    node_dumper.dump_yaml(process_node=calcjob_node, output_path=output_path)

    return True


def workchain_dump(
    process_node: WorkChainNode | CalcJobNode,
    output_path: Path = Path(),
    no_node_inputs: bool = False,
    use_presubmit: bool = False,
    node_dumper: ProcessNodeYamlDumper | None = None,
    overwrite: bool = True,
) -> bool:
    """Dumps all data involved in a `WorkChainNode`, including its outgoing links.

    Note that if an outgoing link is again a `WorkChainNode`, the function recursively calls itself, while files are
    only actually created when a `CalcJobNode` is reached.

    :param process_node: The parent process node to be dumped. It can be either a `WorkChainNode` or a `CalcJobNode`.
    :param output_path: The main output path where the directory tree will be created.
    :param no_node_inputs: If True, do not include file or folder inputs in the dump. Defaults to False.
    :param use_presubmit: If True, use the `prepare_for_submission` method to get the inputs of the
    CalcJobNode. Defaults to False.
    :param node_dumper: The ProcessNodeYamlDumper instance to use for dumping node metadata. If not provided, a new
        instance will be created. Defaults to None.
    :return: bool
    """

    # Keep track of dumping success to be able to communicate it outwards
    all_processes_dumped = True

    # ? Realized during testing: If no path provided, only for the sub-workchain an additional directory is created, but
    # ? should also create one here, if the function is imported normally and used in Python scripts
    output_path = validate_make_dump_path(path=output_path, overwrite=overwrite)

    # This will eventually be replaced once pydantic backend PR merged
    if node_dumper is None:
        node_dumper = ProcessNodeYamlDumper()
    node_dumper.dump_yaml(process_node=process_node, output_path=output_path.resolve())

    # Don't increment index for `ProcessNodes` that don't (always?) have file IO
    # (`CalcFunctionNodes`/`WorkFunctionNodes`), such as `create_kpoints_from_distance`
    called_links = process_node.base.links.get_outgoing(link_type=(LinkType.CALL_CALC, LinkType.CALL_WORK)).all()
    called_links = [
        called_link
        for called_link in called_links
        if not isinstance(called_link.node, (CalcFunctionNode, WorkFunctionNode))
    ]

    for index, link_triple in enumerate(sorted(called_links, key=lambda link_triple: link_triple.node.ctime), start=1):
        child_node = link_triple.node
        child_label = generate_node_input_label(index=index, link_triple=link_triple)

        output_path_child = output_path.resolve() / child_label

        # Recursive function call for `WorkChainNode``
        if isinstance(child_node, WorkChainNode):
            process_dumped = workchain_dump(
                process_node=child_node,
                output_path=output_path_child,
                no_node_inputs=no_node_inputs,
                use_presubmit=use_presubmit,
                node_dumper=node_dumper,
            )

        # Dump for `CalcJobNode`
        elif isinstance(child_node, CalcJobNode):
            process_dumped = calcjob_dump(
                calcjob_node=child_node,
                output_path=output_path_child,
                no_node_inputs=no_node_inputs,
                use_presubmit=use_presubmit,
                node_dumper=node_dumper,
            )

        else:
            process_dumped = False

        all_processes_dumped = all_processes_dumped and process_dumped

    return all_processes_dumped


# Separate functions for CalcJob dumping using pre_submit, as well as for the node_inputs
def calcjob_node_inputs_dump(calcjob_node: CalcJobNode, output_path: Path, inputs_relpath: Path = Path('node_inputs')):
    """Dump inputs of a `CalcJobNode` of type `SinglefileData` and `FolderData`.

    :param calcjob_node: The `CalcJobNode` whose inputs will be dumped.
    :type calcjob_node: CalcJobNode
    :param output_path: The path where the inputs will be dumped.
    :type output_path: Path
    """
    dump_types = (SinglefileData, FolderData)

    # ? Not using the `node_class` argument of `get_incoming`, as it does not actually retrieve, e.g. a `UpfData` node
    # ? (due to planned deprecation?)
    # ? Instead, check for isinstance of `SinglefileData`
    input_node_triples = calcjob_node.base.links.get_incoming(link_type=LinkType.INPUT_CALC)

    for input_node_triple in input_node_triples:
        # Select only repositories that hold objects and are of the selected dump_types
        if len(input_node_triple.node.base.repository.list_objects()) > 0 and isinstance(
            input_node_triple.node, dump_types
        ):
            # input_node_path = output_path / Path('node_inputs') / Path(input_node_triple.link_label)
            input_node_path = output_path / inputs_relpath / Path(*input_node_triple.link_label.split('__'))
            input_node_triple.node.base.repository.copy_tree(input_node_path)


def calcjob_presubmit_dump(calcjob_node: CalcJobNode, output_path: Path):
    """
    Dump inputs of a `CalcJobNode` using the `presubmit` function.

    :param process: The `CalcJobNode` whose inputs need to be dumped.
    :type process: CalcJobNode
    :param output_path: The path where the inputs will be dumped.
    :type output_path: Path
    """

    builder_restart = calcjob_node.get_builder_restart()
    runner = get_manager().get_runner()
    calcjob_process: CalcJob = instantiate_process(runner, builder_restart)  # type: ignore[assignment]

    # `presubmit` calls `prepare_for_submission` internally
    calc_info = calcjob_process.presubmit(folder=Folder(abspath=output_path))

    try:
        # Hackish way to modify local copy list so that the pseudos are actually dumped where I want them to. Otherwise
        # they
        # end up in home...
        local_copy_list = calc_info['local_copy_list'].copy()
        # print('LOCAL_COPY_LIST', local_copy_list)
        new_local_copy_list = [tuple(list(local_copy_list[0][:2]) + [str(output_path / local_copy_list[0][-1])])]
        calc_info['local_copy_list'] = new_local_copy_list
        # print('NEW_LOCAL_COPY_LIST', new_local_copy_list)
    except IndexError:
        # This happens if `local_copy_list` is empty
        pass

    local_transport = LocalTransport().open()
    new_calcjob_node: CalcJobNode = calcjob_process.node
    upload_calculation(
        node=new_calcjob_node,
        transport=local_transport,
        calc_info=calc_info,
        folder=Folder(abspath=output_path),
        inputs=calcjob_process.inputs,
        dry_run=False,
    )
