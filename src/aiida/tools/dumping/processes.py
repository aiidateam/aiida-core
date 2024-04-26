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

import logging
import textwrap
from pathlib import Path

import yaml

from aiida.common import LinkType
from aiida.orm import (
    CalcFunctionNode,
    CalcJobNode,
    CalculationNode,
    FolderData,
    ProcessNode,
    RemoteData,
    SinglefileData,
    UpfData,
    WorkChainNode,
    WorkflowNode,
    WorkFunctionNode,
)
from aiida.orm.utils import LinkTriple
from aiida.repository import File

_LOGGER = logging.getLogger(__name__)
FILE_NODES = (SinglefileData, FolderData, RemoteData, UpfData)
ALL_AIIDA_NODES = True

# todo: Add aiida_nodes as an optional input to cmd_process, and as a class attribute of the dumper that is passed
# todo: through, just like flat

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
        if self.include_attributes:
            node_attributes = process_node.base.attributes.all
            node_dict['Node attributes'] = node_attributes

        # Add node extras
        if self.include_extras:
            node_extras = process_node.base.extras.all
            if node_extras:
                node_dict['Node extras'] = node_extras

        output_file = output_path.resolve() / output_filename
        with open(output_file, 'w') as handle:
            yaml.dump(node_dict, handle, sort_keys=False)


# Utility functions
def generate_dump_readme(process_node: ProcessNode, output_path: Path):
    """Generate README file in main dumping directory.

    :param process_node: CalcJob or WorkChain Node.
    :param output_path: Output path for dumping.

    """

    from aiida.cmdline.utils.ascii_vis import format_call_graph
    from aiida.cmdline.utils.common import (
        get_calcjob_report,
        get_node_info,
        get_process_function_report,
        get_workchain_report,
    )

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

    Lastly, every folder also contains a hidden, human-readable `.aiida_node_metadata.yaml` file with the relevant AiiDA
    node data for further inspection."""  # noqa: E501
    )

    # `verdi process status`
    process_status = format_call_graph(calc_node=process_node, max_depth=None, call_link_label=True)
    _readme_string += f'\n\nOutput of `verdi process status`\n\n{process_status}'

    # `verdi process report`
    # Copied over from `cmd_process`
    if isinstance(process_node, CalcJobNode):
        process_report = get_calcjob_report(process_node)
    elif isinstance(process_node, WorkChainNode):
        process_report = get_workchain_report(process_node, levelname='REPORT', indent_size=2, max_depth=None)
    elif isinstance(process_node, (CalcFunctionNode, WorkFunctionNode)):
        process_report = get_process_function_report(process_node)
    else:
        process_report = f'Nothing to show for node type {process_node.__class__}'

    _readme_string += f'\n\nOutput of `verdi process report`\n\n{process_report}'

    # `verdi process show`?
    process_show = get_node_info(node=process_node)
    _readme_string += f'\n\nOutput of `verdi process show`\n\n{process_show}'

    (output_path / 'README').write_text(_readme_string)


def generate_default_dump_path(process_node: ProcessNode) -> Path:
    """Simple helper function to generate the default parent-dumping directory if none given.

    This function is not called for the sub-calls of `calcjob_node_dump` or during the recursive `process_dump` as it
    just creates the default parent folder for the dumping, if no name is given.

    :param process_node: The `ProcessNode` for which the directory is created.
    :return: The created parent dump path.
    """

    try:
        return Path(f'dump-{process_node.process_label}-{process_node.pk}')
    except AttributeError:
        # ? This case came up during testing, not sure how relevant it actually is
        return Path(f'dump-{process_node.process_type}-{process_node.pk}')


# ? Could move this to `cmdline/utils`
def validate_make_dump_path(
    path: Path, overwrite: bool = False, safeguard_file: str = '.aiida_node_metadata.yaml'
) -> Path:
    """
    Create default dumping directory for a given process node and return it as absolute path.

    :param path: The base path for the dump. Defaults to the current directory.
    :return: The created dump path.
    """
    import shutil

    if path.is_dir():
        # Existing, but empty directory => OK
        if not any(path.iterdir()):
            pass

        # Existing and non-empty directory and overwrite False => FileExistsError
        elif not overwrite:
            raise FileExistsError(f'Path `{path}` already exists and overwrite set to False.')

        # Existing and non-empty directory and overwrite True => Check for '.aiida_node_metadata.yaml' for safety
        # '.aiida_node_metadata.yaml' present => Remove directory
        elif (path / safeguard_file).is_file():
            _LOGGER.info(f'Overwrite set to true, will overwrite directory `{path}`.')
            shutil.rmtree(path)
            path.mkdir(parents=True, exist_ok=False)

        # Existing and non-empty directory and overwrite True => Check for safeguard_file (e.g.
        # '.aiida_node_metadata.yaml') for safety  reasons (don't wont to recursively delete wrong directory...)
        else:
            # _LOGGER.critical(
            #     f"`{path}` Path exists but no `.aiida_node_metadata.yaml` found. Won't delete for security.\n"
            #     # f'Manually remove existing `{path}` and dump again.'
            # )
            raise FileExistsError(
                f"Path `{path}` already exists and doesn't contain `.aiida_node_metadata.yaml`. Not removing for safety reasons."
            )

    # Not included in else as to avoid having to repeat the `mkdir` call. `exist_ok=True` as checks implemented above
    path.mkdir(exist_ok=True, parents=True)

    return path.resolve()


def generate_node_input_label(index: int, link_triple: LinkTriple, flat: bool = False) -> str:
    """Small helper function to generate the directory label for node inputs."""
    node = link_triple.node
    link_label = link_triple.link_label

    # Generate directories with naming scheme akin to `verdi process status`
    # node_label = f'{index:02d}-{link_label}'
    label_list = [f'{index:02d}', link_label]

    try:
        process_label = node.process_label
        if process_label is not None and process_label != link_label:
            label_list += [process_label]
            # node_label += f'-{process_label}'

    except AttributeError:
        process_type = node.process_type
        if process_type is not None and process_type != link_label:
            label_list += [process_type]
            # node_label += f'-{process_type}'

    if isinstance(node, File):
        label_list += [node.name]

    node_label = '-'.join(label_list)
    # `CALL-` as part of the link labels also for MultiplyAddWorkChain -> Seems general enough, so remove
    node_label = node_label.replace('CALL-', '')

    return node_label


def generate_calcjob_io_dump_paths(calcjob_io_dump_paths: list | None = None, flat: bool = False):

    default_calcjob_io_dump_paths = ['raw_inputs', 'raw_outputs', 'node_inputs']

    if flat and calcjob_io_dump_paths is None:
        calcjob_io_dump_paths = ['', '', '']
        _LOGGER.info(
            'Flat set to True and no `io_dump_paths`. Dumping in a flat directory, files might be overwritten.'
        )
    elif flat and calcjob_io_dump_paths is not None:
        _LOGGER.info('Flat set to True but `io_dump_paths` provided. These will be used, but `node_inputs` not nested.')
        calcjob_io_dump_paths = default_calcjob_io_dump_paths
    elif not flat and calcjob_io_dump_paths is None:
        _LOGGER.info(
            f'Flat set to False but no `io_dump_paths` provided. Will use the defaults {default_calcjob_io_dump_paths}.'
        )
        calcjob_io_dump_paths = default_calcjob_io_dump_paths
    # elif not flat and calcjob_io_dump_paths is not None:
    else:
        _LOGGER.info(
            'Flat set to False but no `io_dump_paths` provided. These will be used, but `node_inputs` flattened.'
        )
        calcjob_io_dump_paths = ['', '', '']

    return calcjob_io_dump_paths


def calculation_node_dump(
    calcjob_node: CalculationNode,
    output_path: Path | None,
    include_inputs: bool = True,
    node_dumper: ProcessNodeYamlDumper | None = None,
    overwrite: bool = True,
    flat: bool = False,
    io_dump_paths: list | None = None,
):
    """
    Dump the contents of a CalcJobNode to a specified output path.

    :param calcjob_node: The CalcJobNode to be dumped.
    :param output_path: The path where the dumped contents will be stored.
    :param include_inputs: If True, do not dump the inputs of the CalcJobNode.
    :return: None
    """

    if output_path is None:
        output_path = generate_default_dump_path(process_node=calcjob_node)

    try:
        validate_make_dump_path(path=output_path, overwrite=overwrite)
    except:
        # raise same exception here to communicate it outwards
        raise

    io_dump_paths = generate_calcjob_io_dump_paths(calcjob_io_dump_paths=io_dump_paths, flat=flat)

    # These are the raw_inputs
    calcjob_node.base.repository.copy_tree(output_path.resolve() / io_dump_paths[0])

    # These are the node_inputs
    if include_inputs:
        calculation_node_inputs_dump(calculation_node=calcjob_node, output_path=output_path / io_dump_paths[2], flat=flat)

    output_nodes = [calcjob_node.outputs[output] for output in calcjob_node.outputs]
    for output_node in output_nodes:
        if isinstance(output_node, FILE_NODES):
            output_node.base.repository.copy_tree(output_path.resolve() / io_dump_paths[1])
        elif ALL_AIIDA_NODES:
                output_node.base.repository.copy_tree(output_path.resolve() / io_dump_paths[1] / '.aiida_nodes')

    # This will eventually be replaced once pydantic backend PR merged
    if node_dumper is None:
        node_dumper = ProcessNodeYamlDumper()
    node_dumper.dump_yaml(process_node=calcjob_node, output_path=output_path)


def process_node_dump(
    process_node: ProcessNode,
    output_path: Path | None,
    include_inputs: bool = True,
    node_dumper: ProcessNodeYamlDumper | None = None,
    overwrite: bool = True,
    flat: bool = False,
):
    """Dumps all data involved in a `WorkChainNode`, including its outgoing links.

    Note that if an outgoing link is again a `WorkChainNode`, the function recursively calls itself, while files are
    only actually created when a `CalcJobNode` is reached.

    :param process_node: The parent process node to be dumped. It can be either a `WorkChainNode` or a `CalcJobNode`.
    :param output_path: The main output path where the directory tree will be created.
    :param include_inputs: If True, include file or folder inputs in the dump. Defaults to True.
    :param node_dumper: The ProcessNodeYamlDumper instance to use for dumping node metadata. If not provided, a new
        instance will be created. Defaults to None.
    """

    # Realized during testing: If no path provided, only for the sub-workchain an additional directory is created, but
    # should also create one here, if the function is imported normally and used in Python scripts
    if output_path is None:
        output_path = generate_default_dump_path(process_node=process_node)

    try:
        validate_make_dump_path(path=output_path, overwrite=overwrite)
    except:
        raise

    # This will eventually be replaced once pydantic backend PR merged
    if node_dumper is None:
        node_dumper = ProcessNodeYamlDumper()

    # Need to dump for parent ProcessNode, as well, otherwise no metadata file in parent ProcessNode directory
    node_dumper.dump_yaml(process_node=process_node, output_path=output_path.resolve())

    # This seems a bit duplicated, but if the logic for checking the types should be contained in the recursive
    # `process_dump` function called by `verdi`, then I need to dump for a `CalcJob` here, as
    # well. Also, if I want to be able to use `process_dump` via the Python API
    if isinstance(process_node, (CalcFunctionNode, CalcJobNode)):
        calculation_node_dump(
            calcjob_node=process_node,
            output_path=output_path,
            include_inputs=include_inputs,
            node_dumper=node_dumper,
            overwrite=overwrite,
            flat=flat,
        )

    elif isinstance(process_node, WorkflowNode):
        called_links = process_node.base.links.get_outgoing(link_type=(LinkType.CALL_CALC, LinkType.CALL_WORK)).all()

        # If multiple CalcJobs contained in Workchain flat=True doesn't make sense as files would be overwritten
        # -> Well, if different CalcJobs run, it could still make sense, but would one really want all these files in
        # one flat directory?
        called_calcjobs = [isinstance(node, CalcJobNode) for node in process_node.called_descendants]
        if flat and called_calcjobs.count(True) > 1:
            # Add error message here or when capturing `NotImplementedError`
            raise NotImplementedError

        sorted_called_links = sorted(called_links, key=lambda link_triple: link_triple.node.ctime)

        for index, link_triple in enumerate(sorted_called_links, start=1):
            child_node = link_triple.node
            # if not flat:
            child_label = generate_node_input_label(index=index, link_triple=link_triple, flat=flat)
            # else:
            #     child_label = ''

            child_output_path = output_path.resolve() / child_label

            # Recursive function call for `WorkChainNode``
            # Not sure if the next two cases work for `WorkFunction` and `CalcFuncion``Node`s
            if isinstance(child_node, WorkflowNode):
                process_node_dump(
                    process_node=child_node,
                    output_path=child_output_path,
                    include_inputs=include_inputs,
                    node_dumper=node_dumper,
                    overwrite=overwrite,
                    flat=flat,
                )

            elif isinstance(child_node, CalculationNode):
                calculation_node_dump(
                    calcjob_node=child_node,
                    output_path=child_output_path,
                    include_inputs=include_inputs,
                    node_dumper=node_dumper,
                    overwrite=overwrite,
                    flat=flat,
                )


def calculation_node_inputs_dump(calculation_node: CalculationNode, output_path: Path, flat: bool = False):
    """Dump inputs of a `CalcJobNode`.

    :param calcjob_node: The `CalcJobNode` whose inputs will be dumped.
    :param output_path: The path where the inputs will be dumped.
    :param flat: Dump node inputs in a flat directory structure.
    """

    input_node_triples = calculation_node.base.links.get_incoming(link_type=LinkType.INPUT_CALC)

    for input_node_triple in input_node_triples:
        # Select only repositories that actually hold objects
        # todo: Could make this a separate function
        # Here, the check for repository could also serve a

        input_node_path = generate_input_node_path(input_node_triple=input_node_triple, parent_path=output_path, flat=flat)

        input_node_triple.node.base.repository.copy_tree(input_node_path.resolve())


def generate_input_node_path(input_node_triple, parent_path, flat, exception_labels: list | None = None):

    input_node = input_node_triple.node
    link_label = input_node_triple.link_label

    if exception_labels is None:
        exception_labels = ['pseudos']

    if len(input_node.base.repository.list_objects()) > 0:
        # Empty repository, so it should be standard AiiDA data types, like Int, Float, etc.
        aiida_nodes_subdir = ''
    else:
        aiida_nodes_subdir = '.aiida_nodes'

    # ? The check if the link_label starts with pseudo is again very specific for the atomistic community/QE,
    # ? however, I don't know how to otherwise avoid that it's put in `.aiida_nodes`, as the Node is  defined as
    # ? Data, not UpfData, so I cannot just check against FILE_NODES
    if isinstance(input_node, FILE_NODES) or any(link_label.startswith(label) for label in exception_labels):
        if not flat:
            input_node_path = parent_path / Path(*link_label.split('__'))
        else:
            # Don't use link_label at all -> But, relative path inside FolderData is retained
            input_node_path = parent_path
    elif not flat:
        input_node_path = parent_path / aiida_nodes_subdir / Path(*link_label.split('__'))
    else:
        # Don't use link_label at all -> But, relative path inside FolderData is retained
        input_node_path = parent_path / aiida_nodes_subdir

    return input_node_path.resolve()
