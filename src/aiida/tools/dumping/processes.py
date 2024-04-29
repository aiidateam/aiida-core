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
from pathlib import Path
from typing import Any, List, Optional

import yaml

from aiida.common import LinkType
from aiida.orm import (
    CalcFunctionNode,
    CalcJobNode,
    CalculationNode,
    FolderData,
    ProcessNode,
    SinglefileData,
    WorkChainNode,
    WorkflowNode,
    WorkFunctionNode,
)
from aiida.orm.utils import LinkManager, LinkTriple

# Include RemoteData here? -> Don't think so
FILE_CLASSES = (SinglefileData, FolderData)
LOGGER = logging.getLogger(__name__)


class ProcessDumper:
    def __init__(
        self,
        parent_process: Optional[ProcessNode] = None,
        parent_path: Optional[Path] = None,
        include_node_inputs: bool = True,
        include_attributes: bool = True,
        include_extras: bool = True,
        overwrite: bool = True,
        flat: bool = False,
        all_aiida_nodes: bool = False,
    ) -> None:
        self.parent_process = parent_process
        self.include_node_inputs = include_node_inputs
        self.include_attributes = include_attributes
        self.include_extras = include_extras
        self.overwrite = overwrite
        self.flat = flat
        self.all_aiida_nodes = all_aiida_nodes

        # Automatically determine parent_path on instantiation if `parent_process` is set
        if parent_path is None and parent_process is not None:
            self.parent_path = self.generate_default_dump_path(process_node=self.parent_process)
        elif parent_path is not None:
            self.parent_path = parent_path

    def dump(
        self,
        process_node,  # ? This changes, so it should not be defined as a class variable
        output_path: Path | None,
        io_dump_paths: list | None = None,
    ):
        """Dumps all data involved in a `WorkChainNode`, including its outgoing links.

        Note that if an outgoing link is again a `WorkChainNode`, the function recursively calls itself, while files are
        only actually created when a `CalcJobNode` is reached.

        :param process_node: The parent process node to be dumped. It can be either `WorkChainNode` or `CalcJobNode`
        :param output_path: The main output path where the directory tree will be created.
        :param include_inputs: If True, include file or folder inputs in the dump. Defaults to True.
        :param node_dumper: The ProcessNodeYamlDumper instance to use for dumping node metadata. If not provided, a new
            instance will be created. Defaults to None.
        """

        if output_path is None:
            output_path = self.generate_default_dump_path(process_node=process_node)

        try:
            self.validate_make_dump_path(validate_path=output_path)
        except:
            raise

        # This seems a bit duplicated, but if the logic for checking the types should be contained in the recursive
        # `dump` function called by `verdi`, then I need to dump for the `CalcFunction` here already, as well.
        self.dump_node_yaml(process_node=process_node, output_path=output_path)
        if isinstance(process_node, CalcFunctionNode):
            self._dump_calculation(
                calculation_node=process_node,
                output_path=output_path,
                io_dump_paths=io_dump_paths,
            )

        elif isinstance(process_node, WorkflowNode):
            called_links = process_node.base.links.get_outgoing(
                link_type=(LinkType.CALL_CALC, LinkType.CALL_WORK)
            ).all()

            sorted_called_links = sorted(called_links, key=lambda link_triple: link_triple.node.ctime)

            for index, link_triple in enumerate(sorted_called_links, start=1):
                child_node = link_triple.node
                child_label = self.generate_child_node_label(index=index, link_triple=link_triple)
                child_output_path = output_path.resolve() / child_label

                # Recursive function call for `WorkFlowNode``
                if isinstance(child_node, WorkflowNode):
                    self.dump(
                        process_node=child_node,
                        output_path=child_output_path,
                    )

                # Once a `CalculationNode` as child reached, dump it
                elif isinstance(child_node, CalculationNode):
                    self._dump_calculation(
                        calculation_node=child_node,
                        output_path=child_output_path,
                    )

    def _dump_calculation(
        self,
        calculation_node: CalculationNode,
        output_path: Path | None,
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
            output_path = self.generate_default_dump_path(process_node=calculation_node)

        try:
            self.validate_make_dump_path(validate_path=output_path)
        except:
            # raise same exception here to communicate it outwards
            raise

        self.dump_node_yaml(process_node=calculation_node, output_path=output_path)

        io_dump_mapping = self.generate_calculation_io_mapping(io_dump_paths=io_dump_paths)

        # Dump the repository contents of the node
        # ? Rename this to node_repository or something -> Introduces AiiDA terminology.But as we provide the option to
        # ? dump *all* the outputs, we should also provide the option to dump *all* the inputs, not just `node_inputs`
        calculation_node.base.repository.copy_tree(output_path.resolve() / io_dump_mapping.repository)

        # Dump the extra_inputs
        if self.include_node_inputs:
            input_node_triples = calculation_node.base.links.get_incoming(link_type=LinkType.INPUT_CALC)
            self._dump_calculation_io(parent_path=output_path / io_dump_mapping.inputs, node_triples=input_node_triples)

        # Dump the raw_outputs
        output_node_triples = calculation_node.base.links.get_outgoing(link_type=LinkType.CREATE)
        self._dump_calculation_io(
            parent_path=output_path / io_dump_mapping.outputs,
            node_triples=output_node_triples,
        )

    def _dump_calculation_io(self, parent_path: Path, node_triples: LinkManager):
        # if exception_paths is None:
        #     exception_paths = ['/pseudos/']

        for node_triple in node_triples:
            node = node_triple.node
            if isinstance(node, FILE_CLASSES) or any(issubclass(type(node), cls) for cls in FILE_CLASSES):
                file_node_path = self.generate_link_triple_dump_path(
                    link_triple=node_triple,
                    parent_path=parent_path,
                )

                # No .resolve() required as that done in `generate_calcjob_input_node_path`
                node_triple.node.base.repository.copy_tree(file_node_path)

            else:
                aiida_node_path = self.generate_link_triple_dump_path(
                    link_triple=node_triple,
                    parent_path=parent_path / '.aiida_nodes',
                )

                # This is again QE specific, but, frankly, I don't know how to otherwise separate the pseudos from the
                # rest of the AiiDA-nodes, as the pseudos are of `Data` type (why not UpfData?), so I cannot distinguish
                # them from other AiiDA-nodes, such as ArrayData which we definitely want in the hidden `.aiida_nodes`
                # subdirectory
                # So if anybody has a better solution, I'd be happy to use that
                # The problem might be void, though, once all the atomistic code is moved to `aiida-atomistic`
                if node.node_type == 'data.pseudo.upf.UpfData.':
                    node_triple.node.base.repository.copy_tree(Path(str(aiida_node_path).replace('.aiida_nodes', '')))
                elif self.all_aiida_nodes:
                    node_triple.node.base.repository.copy_tree(aiida_node_path)

    def validate_make_dump_path(self, validate_path: Path, safeguard_file: str = '.aiida_node_metadata.yaml') -> Path:
        """
        Create default dumping directory for a given process node and return it as absolute path.

        :param path: The base path for the dump. Defaults to the current directory.
        :return: The created dump path.
        """
        import shutil

        if validate_path.is_dir():
            # Existing, empty directory -> OK
            if not any(validate_path.iterdir()):
                pass

            # Existing, non-empty directory and overwrite False -> FileExistsError
            elif not self.overwrite:
                raise FileExistsError(f'Path `{validate_path}` already exists and overwrite set to False.')

            # Existing, non-empty directory and overwrite True
            # Check for safeguard file ('.aiida_node_metadata.yaml') for safety
            # If present -> Remove directory
            elif (validate_path / safeguard_file).is_file():
                LOGGER.info(f'Overwrite set to true, will overwrite directory `{validate_path}`.')
                shutil.rmtree(validate_path)

            # Existing and non-empty directory and overwrite True
            # Check for safeguard file ('.aiida_node_metadata.yaml') for safety
            # If absent -> Don't remove directory as to not accidentally remove a wrong one
            else:
                raise FileExistsError(
                    f"Path `{validate_path}` already exists and doesn't contain safeguard file {safeguard_file}."
                    f'Not removing for safety reasons.'
                )

        # Not included in if-else as to avoid having to repeat the `mkdir` call.
        # `exist_ok=True` as checks implemented above
        validate_path.mkdir(exist_ok=True, parents=True)

        return validate_path.resolve()

    def generate_default_dump_path(self, process_node: ProcessNode | None) -> Path:
        """Simple helper function to generate the default parent-dumping directory if none given.

        This function is not called for the sub-calls of `calcjob_node_dump` or during the recursive `process_dump` as
        it just creates the default parent folder for the dumping, if no name is given.

        :param process_node: The `ProcessNode` for which the directory is created.
        :return: The created parent dump path.
        """
        if process_node is None:
            raise TypeError('`process_node` must be provided for generating the default path.')
        else:
            pk = process_node.pk
            try:
                return Path(f'dump-{process_node.process_label}-{pk}')
            except AttributeError:
                # ? This case came up during testing, not sure how relevant it actually is
                return Path(f'dump-{process_node.process_type}-{pk}')

    def generate_calculation_io_mapping(self, io_dump_paths: Optional[List[Any]] = None):
        # Could turn this into a dict/mapping and use as labels what the entities actually refer to
        # Don't use AiiDA terminology directly as it might be confusing for other users who are mainly targeted for the
        # dumping
        # ? Could move this outside of class and just pass flat, and not set the logger as a class attribute

        from types import SimpleNamespace

        aiida_entities_to_dump = ['repository', 'inputs', 'outputs']
        default_calculation_io_dump_paths = ['raw_inputs', 'extra_inputs', 'raw_outputs']
        empty_calculation_io_dump_paths = [''] * 3

        if self.flat and io_dump_paths is None:
            LOGGER.info(
                'Flat set to True and no `io_dump_paths`. Dumping in a flat directory, files might be overwritten.'
            )
            return SimpleNamespace(**dict(zip(aiida_entities_to_dump, empty_calculation_io_dump_paths)))

        elif not self.flat and io_dump_paths is None:
            LOGGER.info(
                'Flat set to False but no `io_dump_paths` provided. '
                + f'Will use the defaults {default_calculation_io_dump_paths}.'
            )
            return SimpleNamespace(**dict(zip(aiida_entities_to_dump, default_calculation_io_dump_paths)))

        elif self.flat and io_dump_paths is not None:
            LOGGER.info(
                'Flat set to True but `io_dump_paths` provided. These will be used, but `node_inputs` not nested.'
            )
            return SimpleNamespace(**dict(zip(aiida_entities_to_dump, io_dump_paths)))
        else:
            LOGGER.info(
                'Flat set to False but no `io_dump_paths` provided. These will be used, but `node_inputs` flattened.'
            )
            return SimpleNamespace(**dict(zip(aiida_entities_to_dump, io_dump_paths)))  # type: ignore[arg-type]

    def generate_link_triple_dump_path(self, link_triple: LinkTriple, parent_path: Path) -> Path:
        node = link_triple.node
        link_label = link_triple.link_label
        # For convenience, remove the 'retrieved' subdirectory for the outputs
        link_label = link_label.replace('retrieved', '')

        # This is again QE specific...
        # if exception_labels is None:
        #     exception_labels = ['pseudos']

        # ? Shouldn't this be only be applied to `CalculationNode`s?
        # This check is necessary, as I'm now not only dumping the 'retrieved' outputs and file-based inputs, but all of
        # the connected links if self.all_aiida_nodes is True
        # ? This is now handled outside, before this function is called
        # if len(node.base.repository.list_objects()) > 0:
        #     aiida_nodes_subdir = ''
        # else:
        #     # Empty repository, so it should be non-file-based AiiDA data types, like ArrayData
        #     # -> Put those into '.aiida_nodes' subdirectory
        #     aiida_nodes_subdir = '.aiida_nodes'
        # # aiida_nodes_subdir = ''

        # ? The check if the link_label starts with pseudo is again very specific for the atomistic community/QE,
        # ? however, I don't know how to otherwise avoid that it's put in `.aiida_nodes`, as the Node is  defined as
        # ? Data, not UpfData, so I cannot just check against FILE_NODES
        # if isinstance(node, FILE_CLASSES) or any(link_label.startswith(label) for label in exception_labels):
        if isinstance(node, FILE_CLASSES):
            if not self.flat:
                input_node_path = parent_path / Path(*link_label.split('__'))
            else:
                # Don't use link_label at all -> But, relative path inside FolderData is retained
                input_node_path = parent_path
        elif not self.flat:
            # input_node_path = parent_path / aiida_nodes_subdir / Path(*link_label.split('__'))
            input_node_path = parent_path / Path(*link_label.split('__'))
        else:
            # Don't use link_label at all -> But, relative path inside FolderData is retained
            # input_node_path = parent_path / aiida_nodes_subdir
            input_node_path = parent_path

        return input_node_path.resolve()

    def generate_child_node_label(self, index: int, link_triple: LinkTriple) -> str:
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

        # if isinstance(node, File):
        #     label_list += [node.name]

        node_label = '-'.join(label_list)
        # `CALL-` as part of the link labels also for MultiplyAddWorkChain -> Seems general enough, so remove
        node_label = node_label.replace('CALL-', '')
        node_label = node_label.replace('None-', '')

        return node_label

    def dump_node_yaml(
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

        _node_properties = [
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

        _user_properties = ('first_name', 'last_name', 'email', 'institution')

        _computer_properties = ('label', 'hostname', 'scheduler_type', 'transport_type')

        node_dict = {}
        metadata_dict = {}

        # Add actual node `@property`s to dictionary
        for metadata_property in _node_properties:
            metadata_dict[metadata_property] = getattr(process_node, metadata_property)

        node_dict['Node data'] = metadata_dict

        # Add user data
        try:
            node_dbuser = process_node.user
            user_dict = {}
            for user_property in _user_properties:
                user_dict[user_property] = getattr(node_dbuser, user_property)
            node_dict['User data'] = user_dict
        except AttributeError:
            pass

        # Add computer data
        try:
            node_dbcomputer = process_node.computer
            computer_dict = {}
            for computer_property in _computer_properties:
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

    # ? Add type hints here? Would require loading from ORM in header of `cmd_` file -> Might fail CLI time validation
    def generate_parent_readme(self):
        """Generate README file in main dumping directory.

        :param process_node: CalcJob or WorkChain Node.
        :param output_path: Output path for dumping.

        """

        import textwrap

        from aiida.cmdline.utils.ascii_vis import format_call_graph
        from aiida.cmdline.utils.common import (
            get_calcjob_report,
            get_node_info,
            get_process_function_report,
            get_workchain_report,
        )

        if self.parent_process is None or self.parent_path is None:
            raise TypeError('parent_process and parent_path must be set before README can be created.')

        _readme_string = textwrap.dedent(
            f"""\
        This directory contains the files involved in the calculation/workflow `{self.parent_process.process_label} <{self.parent_process.pk}>` run with AiiDA.

        Child calculations/workflows (also called `CalcJob`s and `WorkChain`s in AiiDA jargon) run by the parent workflow are
        contained in the directory tree as sub-folders and are sorted by their creation time. The directory tree thus
        mirrors the logical execution of the workflow, which can also be queried by running `verdi process status
        {self.parent_process.pk}` on the command line.

        By default, input and output files of each simulation can be found in the corresponding "raw_inputs" and
        "raw_outputs" directories (the former also contains the hidden ".aiida" folder with machine-readable job execution
        settings). Additional input files (depending on the type of calculation) are placed in the "extra_inputs".

        Lastly, every folder also contains a hidden, human-readable `.aiida_node_metadata.yaml` file with the relevant AiiDA
        node data for further inspection."""  # noqa: E501
        )

        # `verdi process status`
        process_status = format_call_graph(calc_node=self.parent_process, max_depth=None, call_link_label=True)
        _readme_string += f'\n\n\nOutput of `verdi process status {self.parent_process.pk}:`\n\n{process_status}'

        # `verdi process report`
        # Copied over from `cmd_process`
        if isinstance(self.parent_process, CalcJobNode):
            process_report = get_calcjob_report(self.parent_process)
        elif isinstance(self.parent_process, WorkChainNode):
            process_report = get_workchain_report(
                self.parent_process, levelname='REPORT', indent_size=2, max_depth=None
            )
        elif isinstance(self.parent_process, (CalcFunctionNode, WorkFunctionNode)):
            process_report = get_process_function_report(self.parent_process)
        else:
            process_report = f'Nothing to show for node type {self.parent_process.__class__}'

        _readme_string += f'\n\n\nOutput of `verdi process report {self.parent_process.pk}`:\n\n{process_report}'

        # `verdi process show`?
        process_show = get_node_info(node=self.parent_process)
        _readme_string += f'\n\n\nOutput of `verdi process show {self.parent_process.pk}`:\n\n{process_show}'

        with (self.parent_path / 'README').open('w') as handle:
            handle.write(_readme_string)
