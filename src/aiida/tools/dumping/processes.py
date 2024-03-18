from pathlib import Path
from typing import Union

import yaml

from aiida.cmdline.utils import echo
from aiida.cmdline.utils.defaults import make_default_dump_path
from aiida.common import LinkType
from aiida.common.folders import Folder
from aiida.engine.daemon.execmanager import upload_calculation
from aiida.engine.utils import instantiate_process
from aiida.manage import get_manager
from aiida.orm import CalcFunctionNode, CalcJobNode, WorkChainNode, WorkFunctionNode
from aiida.orm.nodes.data import FolderData, SinglefileData
from aiida.orm.nodes.process import ProcessNode
from aiida.transports.plugins.local import LocalTransport


class ProcessNodeYamlDumper:
    """Utility class to dump selected `ProcessNode` properties and, optionally, attributes and extras to yaml."""

    NODE_PROPERTIES = [
        'label',
        'description',
        # 'pk',
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
        self, process_node: ProcessNode, output_path: Path, output_filename: str = 'aiida_node_metadata.yaml'
    ) -> None:
        """
        Dump the selected `ProcessNode` properties, attributes, and extras to a yaml file.

        :param process_node: The ProcessNode to dump.
        :param output_path: The path to the directory where the yaml file will be saved.
        :param output_filename: The name of the output yaml file. Defaults to 'aiida_node_metadata.yaml'.
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
            node_dbuser = process_node.user._backend_entity.bare_model
            user_dict = {}
            for user_property in self.USER_PROPERTIES:
                user_dict[user_property] = getattr(node_dbuser, user_property)
            node_dict['User data'] = user_dict
        except AttributeError:
            pass

        # Add computer data
        try:
            node_dbcomputer = process_node.computer._backend_entity.bare_model
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
        output_file = output_path / output_filename

        if not output_file.exists():
            with open(output_file, 'w') as handle:
                yaml.dump(node_dict, handle, sort_keys=False)
        else:
            echo.echo_warning(f'yaml file at path "{output_path}" already exists. Skipping.')


def workchain_dump(
    process: Union[WorkChainNode, CalcJobNode],
    output_path: Path = Path(),
    no_node_inputs: bool = False,
    use_prepare_for_submission: bool = False,
    node_dumper: ProcessNodeYamlDumper = None,
) -> None:
    """
    Dumps all data involved in a `WorkChainNode`, including its outgoing links.

    Note that if an outgoing link is again a `WorkChainNode`, the function recursively calls itself, while files are
    only actually created when a `CalcJobNode` is reached.

    :param process_node: The parent process node to be dumped. It can be either a `WorkChainNode` or a `CalcJobNode`.
    :param output_path: The main output path where the directory tree will be created.
    :param no_node_inputs: If True, do not include file or folder inputs in the dump. Defaults to False.
    :param use_prepare_for_submission: If True, use the `prepare_for_submission` method to get the inputs of the
    CalcJobNode. Defaults to False.
    :param node_dumper: The ProcessNodeYamlDumper instance to use for dumping node metadata. If not provided, a new
        instance will be created. Defaults to None.
    :return: None
    """

    # Dump node metadata as yaml
    if node_dumper is None:
        node_dumper = ProcessNodeYamlDumper()
    if isinstance(process, WorkChainNode):
        node_dumper.dump_yaml(process_node=process, output_path=output_path)

    # node_dumper.dump_yaml(process_node=process_node, output_path=output_path)
    called_links = process.base.links.get_outgoing(link_type=(LinkType.CALL_CALC, LinkType.CALL_WORK)).all()

    # Don't increment index for `ProcessNodes`` that don't have file IO (`CalcFunctionNodes`/`WorkFunctionNodes`), such
    # as `create_kpoints_from_distance`
    called_links = [
        called_link
        for called_link in called_links
        if not isinstance(called_link.node, (CalcFunctionNode, WorkFunctionNode))
    ]

    for index, link_triple in enumerate(sorted(called_links, key=lambda link_triple: link_triple.node.ctime), start=1):
        child_node = link_triple.node
        link_label = link_triple.link_label

        # Generate directories with naming scheme akin to `verdi process status`
        if link_label != 'CALL' and not link_label.startswith('iteration_'):
            label = f'{index:02d}-{link_label}-{child_node.process_label}'
        else:
            label = f'{index:02d}-{child_node.process_label}'

        output_path_child = output_path.resolve() / label
        output_path_child.mkdir(exist_ok=True, parents=True)

        # Recursive function call for `WorkChainNode``
        if isinstance(child_node, WorkChainNode):
            workchain_dump(
                process=child_node,
                output_path=output_path_child,
                no_node_inputs=no_node_inputs,
                use_prepare_for_submission=use_prepare_for_submission,
                node_dumper=node_dumper,
            )

        # Dump for `CalcJobNode`
        elif isinstance(child_node, CalcJobNode):
            calcjob_dump(
                process=child_node,
                output_path=output_path_child,
                no_node_inputs=no_node_inputs,
                use_prepare_for_submission=use_prepare_for_submission,
                node_dumper=node_dumper,
            )


def calcjob_dump(
    process: CalcJobNode,
    output_path: Path,
    no_node_inputs: bool = False,
    use_prepare_for_submission: bool = False,
    node_dumper: ProcessNodeYamlDumper = None,
):
    """
    Dump the contents of a CalcJobNode to a specified output path.

    :param calcjob_node: The CalcJobNode to be dumped.
    :param output_path: The path where the dumped contents will be stored.
    :param no_node_inputs: If True, do not dump the inputs of the CalcJobNode.
    :param use_prepare_for_submission: If True, use the `prepare_for_submission` method to prepare the calculation for
        submission. If False, use the retrieved outputs and raw inputs.
    :return: None
    """

    output_path_abs = output_path.resolve()

    if node_dumper is None:
        node_dumper = ProcessNodeYamlDumper()
    node_dumper.dump_yaml(process_node=process, output_path=output_path)

    if use_prepare_for_submission is False:
        # Outputs obtained via retrieved and should not be present when using `prepare_for_submission` as it puts the
        # calculation in a state to be submitted ?!
        process.base.repository.copy_tree(output_path_abs / Path('raw_inputs'))
        process.outputs.retrieved.copy_tree(output_path_abs / Path('raw_outputs'))

        # Dump `SinglefileData` and `FolderData` inputs of the `CalcJobNode`
        if no_node_inputs is False:
            input_node_triples = process.base.links.get_incoming(link_type=LinkType.INPUT_CALC)
            dump_types = (SinglefileData, FolderData)

            for input_node_triple in input_node_triples:
                # Select only repositories that hold objects and are of types
                if len(input_node_triple.node.base.repository.list_objects()) > 0 and isinstance(
                    input_node_triple.node, dump_types
                ):
                    input_node_path = output_path / Path('node_inputs') / Path(input_node_triple.link_label)
                    # Could also create nested path from name mangling?
                    # output_path / Path('node_inputs') / Path(*input_node_triple.link_label.split('__'))

                    input_node_path.mkdir(parents=True, exist_ok=True)
                    input_node_triple.node.base.repository.copy_tree(input_node_path.resolve())

    else:
        echo.echo_warning('`use_prepare_for_submission` not fully implemented yet. Files likely missing.')
        try:
            builder_restart = process.get_builder_restart()
            runner = get_manager().get_runner()
            calcjob_process = instantiate_process(runner, builder_restart)
            calc_info = calcjob_process.presubmit(folder=Folder(abspath=output_path_abs))
            remote_data = upload_calculation(
                node=process,
                transport=LocalTransport(),
                calc_info=calc_info,
                folder=Folder(abspath=output_path_abs),
                inputs=calcjob_process.inputs,
                dry_run=True,
            )

        except ValueError:
            echo.echo_error(
                'ValueError when trying to get a restart-builder. Do you have the relevant aiida-plugin installed?'
            )


def process_dump(
    process_type,
    process: ProcessNode,
    path: Path,
    no_node_inputs: bool = False,
    include_attributes: bool = True,
    include_extras: bool = False,
    use_prepare_for_submission: bool = False,
    overwrite: bool = False,
) -> None:
    """
    Dump the raw files for a given process node. Note that this is just a wrapper around the respective `calcjob_dump`
    and `workchain_dump` functions that provides some type checking and instantiates the YamlDumper and the output path.

    :param process_type: The type of process node to dump (e.g., CalcJobNode, WorkChainNode).
    :param process: The process node to dump.
    :param path: The path where the raw files will be dumped.
    :param no_node_inputs: If True, exclude the inputs of the process node from the dump.
    :param include_attributes: If True, include the attributes of the process node in the dump.
    :param include_extras: If True, include the extras of the process node in the dump.
    :param use_prepare_for_submission: If True, use the `prepare_for_submission` method of the process node
                                       to generate the input files for the dump.
    :param overwrite: If True, overwrite any existing files in the dump path.
    """

    # Instantiate YamlDumper
    processnode_dumper = ProcessNodeYamlDumper(include_attributes=include_attributes, include_extras=include_extras)

    # Make output directory
    output_path = make_default_dump_path(path=path, process_node=process, overwrite=overwrite)

    # Type checking for process with warning if called on the wrong one
    if isinstance(process, process_type):
        dump_function = calcjob_dump if process_type == CalcJobNode else workchain_dump
        dump_function(
            process=process,
            output_path=output_path,
            no_node_inputs=no_node_inputs,
            use_prepare_for_submission=use_prepare_for_submission,
            node_dumper=processnode_dumper,
        )
    else:
        alternative_type = 'CalcJob' if process_type == WorkChainNode else 'WorkChain'
        echo.echo_warning(f'Command called on {alternative_type}Node.')
        echo.echo_warning(
            f'Will dump anyway, but `verdi {alternative_type.lower()} dump <{process.pk}>` should be used instead.'
        )
        dump_function = workchain_dump if process_type == CalcJobNode else calcjob_dump
        dump_function(
            process=process,
            output_path=output_path,
            no_node_inputs=no_node_inputs,
            use_prepare_for_submission=use_prepare_for_submission,
            node_dumper=processnode_dumper,
        )

    echo.echo_report(
        f'Raw files for {process.__class__.__name__} <{process.pk}> dumped successfully in directory "{output_path}".'
    )
