from pathlib import Path
from typing import Union

import yaml

from aiida.cmdline.utils import echo
from aiida.common import LinkType
from aiida.common.exceptions import NotExistentAttributeError
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
        self, process_node: ProcessNode, output_path: Path, output_filename: str = '.aiida_node_metadata.yaml'
    ) -> None:
        """
        Dump the selected `ProcessNode` properties, attributes, and extras to a yaml file.

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
            node_dbuser = process_node.user.backend_entity.bare_model
            user_dict = {}
            for user_property in self.USER_PROPERTIES:
                user_dict[user_property] = getattr(node_dbuser, user_property)
            node_dict['User data'] = user_dict
        except AttributeError:
            pass

        # Add computer data
        try:
            node_dbcomputer = process_node.computer.backend_entity.bare_model
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
        with open(output_file, 'w') as handle:
            yaml.dump(node_dict, handle, sort_keys=False)


def calcjob_node_inputs_dump(process: ProcessNode, output_path: Path, parent_name: str = 'node_inputs'):
    """
    Dump inputs of a `ProcessNode` of type `SinglefileData` and `FolderData`.

    :param process: The `ProcessNode` whose inputs need to be dumped.
    :type process: Union[CalcJobNode, WorkChainNode]
    :param output_path: The path where the inputs will be dumped.
    :type output_path: Path
    """
    dump_types = (SinglefileData, FolderData)

    # Not using the node_class argument of `get_incoming` here, as it does not actually retrieve the `UpfData` node with
    # (due to planned deprecation?)
    # Instead, check for isinstance of `SinglefileData`
    input_node_triples = process.base.links.get_incoming(link_type=LinkType.INPUT_CALC)

    for input_node_triple in input_node_triples:
        # Select only repositories that hold objects and are of the selected dump_types
        if len(input_node_triple.node.base.repository.list_objects()) > 0 and isinstance(
            input_node_triple.node, dump_types
        ):
            # input_node_path = output_path / Path('node_inputs') / Path(input_node_triple.link_label)
            input_node_path = output_path / Path(parent_name) / Path(*input_node_triple.link_label.split('__'))
            # -> The directory contents within each of the 'node_inputs' folders should be fine as done by copy_tree, so
            # no testing required here
            input_node_triple.node.base.repository.copy_tree(input_node_path)


def calcjob_prepare_for_submission_dump(calcjob_node: CalcJobNode, output_path: Path):
    """
    Dump inputs of a `CalcJobNode` using the `presubmit` function.

    :param process: The `CalcJobNode` whose inputs need to be dumped.
    :type process: CalcJobNode
    :param output_path: The path where the inputs will be dumped.
    :type output_path: Path
    """
    try:
        builder_restart = calcjob_node.get_builder_restart()
        runner = get_manager().get_runner()
        calcjob_process = instantiate_process(runner, builder_restart)
        # `presubmit` calls prepare_for_submission internally
        calc_info = calcjob_process.presubmit(folder=Folder(abspath=output_path))
        local_transport = LocalTransport().open()
        upload_calculation(
            node=calcjob_process.node,
            transport=local_transport,
            calc_info=calc_info,
            folder=Folder(abspath=output_path),
            inputs=calcjob_process.inputs,
            dry_run=True,
        )

    except ValueError:
        echo.echo_error(
            'ValueError when trying to get a restart-builder. Do you have the relevant aiida-plugin installed?'
        )


def calcjob_dump(
    calcjob_node: CalcJobNode,
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

    if not use_prepare_for_submission:
        # Outputs obtained via retrieved and should not be present when using `prepare_for_submission` as it puts the
        # calculation in a state to be submitted ?!
        calcjob_node.base.repository.copy_tree(output_path / Path('raw_inputs'))
        try:
            calcjob_node.outputs.retrieved.copy_tree(output_path / Path('raw_outputs'))

        # Might not have an output with link label retrieved
        except NotExistentAttributeError:
            pass

        if not no_node_inputs:
            calcjob_node_inputs_dump(process=calcjob_node, output_path=output_path)

    else:
        echo.echo_warning('`use_prepare_for_submission` not fully implemented yet. Files likely missing.')
        calcjob_prepare_for_submission_dump(calcjob_node=calcjob_node, output_path=output_path)

    # This will eventually be replaced once pydantic backend PR merged
    if node_dumper is None:
        node_dumper = ProcessNodeYamlDumper()
    node_dumper.dump_yaml(process_node=calcjob_node, output_path=output_path)


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

    # .copy_tree() creates the directory, but is only called in `calcjob_dump`, so need to create path here
    if not output_path.exists():
        output_path.mkdir(exist_ok=True, parents=True)

    # This will eventually be replaced once pydantic backend PR merged
    if node_dumper is None:
        node_dumper = ProcessNodeYamlDumper()
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

        output_path_child = output_path / label

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
                calcjob_node=child_node,
                output_path=output_path_child,
                no_node_inputs=no_node_inputs,
                use_prepare_for_submission=use_prepare_for_submission,
                node_dumper=node_dumper,
            )
