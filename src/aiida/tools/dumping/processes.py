###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Functionality for dumping of ProcessNodes."""

from __future__ import annotations

import logging
from pathlib import Path
from types import SimpleNamespace
from typing import List

import yaml

from aiida.common import LinkType
from aiida.common.exceptions import NotExistentAttributeError
from aiida.orm import (
    CalcFunctionNode,
    CalcJobNode,
    CalculationNode,
    LinkManager,
    ProcessNode,
    WorkChainNode,
    WorkflowNode,
    WorkFunctionNode,
)
from aiida.orm.utils import LinkTriple

LOGGER = logging.getLogger(__name__)


class ProcessDumper:
    def __init__(
        self,
        include_inputs: bool = True,
        include_outputs: bool = False,
        include_attributes: bool = True,
        include_extras: bool = True,
        overwrite: bool = False,
        flat: bool = False,
    ) -> None:
        self.include_inputs = include_inputs
        self.include_outputs = include_outputs
        self.include_attributes = include_attributes
        self.include_extras = include_extras
        self.overwrite = overwrite
        self.flat = flat

    @staticmethod
    def _generate_default_dump_path(process_node: ProcessNode) -> Path:
        """Simple helper function to generate the default parent-dumping directory if none given.

        This function is not called for the recursive sub-calls of `_dump_calculation` as it just creates the default
        parent folder for the dumping, if no name is given.

        :param process_node: The `ProcessNode` for which the directory is created.
        :return: The absolute default parent dump path.
        """

        pk = process_node.pk
        try:
            return Path(f'dump-{process_node.process_label}-{pk}')
        except AttributeError:
            # This case came up during testing, not sure how relevant it actually is
            return Path(f'dump-{process_node.process_type}-{pk}')

    @staticmethod
    def _generate_readme(process_node: ProcessNode, output_path: Path) -> None:
        """Generate README.md file in main dumping directory.

        :param process_node: `CalculationNode` or `WorkflowNode`.
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

        pk = process_node.pk

        _readme_string = textwrap.dedent(
            f"""\
        This directory contains the files involved in the calculation/workflow
        `{process_node.process_label} <{pk}>` run with AiiDA.

        Child calculations/workflows (also called `CalcJob`s/`CalcFunction`s and `WorkChain`s/`WorkFunction`s in AiiDA
        jargon) run by the parent workflow are contained in the directory tree as sub-folders and are sorted by their
        creation time. The directory tree thus mirrors the logical execution of the workflow, which can also be queried
        by running `verdi process status {pk}` on the command line.

        By default, input and output files of each calculation can be found in the corresponding "inputs" and "outputs"
        directories (the former also contains the hidden ".aiida" folder with machine-readable job execution settings).
        Additional input and output files (depending on the type of calculation) are placed in the "node_inputs" and
        "node_outputs", respectively.

        Lastly, every folder also contains a hidden, human-readable `.aiida_node_metadata.yaml` file with the relevant
        AiiDA node data for further inspection."""
        )

        # `verdi process status`
        process_status = format_call_graph(calc_node=process_node, max_depth=None, call_link_label=True)
        _readme_string += f'\n\n\nOutput of `verdi process status {pk}`:\n\n```shell\n{process_status}\n```'

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

        _readme_string += f'\n\n\nOutput of `verdi process report {pk}`:\n\n```shell\n{process_report}\n```'

        # `verdi process show`?
        process_show = get_node_info(node=process_node)
        _readme_string += f'\n\n\nOutput of `verdi process show {pk}`:\n\n```shell\n{process_show}\n```'

        (output_path / 'README.md').write_text(_readme_string)

    @staticmethod
    def _generate_child_node_label(index: int, link_triple: LinkTriple) -> str:
        """Small helper function to generate and clean directory label for child nodes during recursion.

        :param index: Index assigned to step at current level of recursion.
        :param link_triple: `LinkTriple` of `ProcessNode` explored during recursion.
        :return: Chlild node label during recursion.
        """
        node = link_triple.node
        link_label = link_triple.link_label

        # Generate directories with naming scheme akin to `verdi process status`
        label_list = [f'{index:02d}', link_label]

        try:
            process_label = node.process_label
            if process_label is not None and process_label != link_label:
                label_list += [process_label]

        except AttributeError:
            process_type = node.process_type
            if process_type is not None and process_type != link_label:
                label_list += [process_type]

        node_label = '-'.join(label_list)
        # `CALL-` as part of the link labels also for MultiplyAddWorkChain -> Seems general enough, so remove
        node_label = node_label.replace('CALL-', '')
        node_label = node_label.replace('None-', '')

        return node_label

    def dump(
        self,
        process_node: ProcessNode,
        output_path: Path | None,
        io_dump_paths: List[str | Path] | None = None,
    ) -> Path:
        """Dumps all data involved in a `ProcessNode`, including its outgoing links.

        Note that if an outgoing link is a `WorkflowNode`, the function recursively calls itself, while files are
        only actually created when a `CalculationNode` is reached.

        :param process_node: The parent `ProcessNode` node to be dumped.
        :param output_path: The output path where the directory tree will be created.
        :param io_dump_paths: Subdirectories created for each `CalculationNode`.
            Default: ['inputs', 'outputs', 'node_inputs', 'node_outputs']
        """

        if output_path is None:
            output_path = self._generate_default_dump_path(process_node=process_node)

        self._validate_make_dump_path(validate_path=output_path)

        if isinstance(process_node, CalculationNode):
            self._dump_calculation(
                calculation_node=process_node,
                output_path=output_path,
                io_dump_paths=io_dump_paths,
            )

        elif isinstance(process_node, WorkflowNode):
            self._dump_workflow(
                workflow_node=process_node,
                output_path=output_path,
                io_dump_paths=io_dump_paths,
            )

        self._generate_readme(process_node=process_node, output_path=output_path)

        return output_path

    def _dump_workflow(
        self, workflow_node: WorkflowNode, output_path: Path, io_dump_paths: List[str | Path] | None = None
    ) -> None:
        """Recursive function to traverse a `WorkflowNode` and dump its `CalculationNode` s.

        :param workflow_node: `WorkflowNode` to be traversed. Will be updated during recursion.
        :param output_path: Dumping parent directory. Will be updated during recursion.
        :param io_dump_paths: Custom subdirectories for `CalculationNode` s, defaults to None
        """

        self._validate_make_dump_path(validate_path=output_path)
        self._dump_node_yaml(process_node=workflow_node, output_path=output_path)

        called_links = workflow_node.base.links.get_outgoing(link_type=(LinkType.CALL_CALC, LinkType.CALL_WORK)).all()
        called_links = sorted(called_links, key=lambda link_triple: link_triple.node.ctime)

        for index, link_triple in enumerate(called_links, start=1):
            child_node = link_triple.node
            child_label = self._generate_child_node_label(index=index, link_triple=link_triple)
            child_output_path = output_path.resolve() / child_label

            # Recursive function call for `WorkFlowNode`
            if isinstance(child_node, WorkflowNode):
                self._dump_workflow(
                    workflow_node=child_node,
                    output_path=child_output_path,
                    io_dump_paths=io_dump_paths,
                )

            # Once a `CalculationNode` as child reached, dump it
            elif isinstance(child_node, CalculationNode):
                self._dump_calculation(
                    calculation_node=child_node,
                    output_path=child_output_path,
                    io_dump_paths=io_dump_paths,
                )

    def _dump_calculation(
        self,
        calculation_node: CalculationNode,
        output_path: Path,
        io_dump_paths: List[str | Path] | None = None,
    ) -> None:
        """Dump the contents of a `CalculationNode` to a specified output path.

        :param calculation_node: The `CalculationNode` to be dumped.
        :param output_path: The path where the files will be dumped.
        :param io_dump_paths: Subdirectories created for the `CalculationNode`.
            Default: ['inputs', 'outputs', 'node_inputs', 'node_outputs']
        """

        self._validate_make_dump_path(validate_path=output_path)
        self._dump_node_yaml(process_node=calculation_node, output_path=output_path)

        io_dump_mapping = self._generate_calculation_io_mapping(io_dump_paths=io_dump_paths)

        # Dump the repository contents of the node
        calculation_node.base.repository.copy_tree(output_path.resolve() / io_dump_mapping.repository)

        # Dump the repository contents of `outputs.retrieved`
        try:
            calculation_node.outputs.retrieved.base.repository.copy_tree(
                output_path.resolve() / io_dump_mapping.retrieved
            )
        except NotExistentAttributeError:
            pass

        # Dump the node_inputs
        if self.include_inputs:
            input_links = calculation_node.base.links.get_incoming(link_type=LinkType.INPUT_CALC)
            self._dump_calculation_io(parent_path=output_path / io_dump_mapping.inputs, link_triples=input_links)

        # Dump the node_outputs apart from `retrieved`
        if self.include_outputs:
            output_links = list(calculation_node.base.links.get_outgoing(link_type=LinkType.CREATE))
            output_links = [output_link for output_link in output_links if output_link.link_label != 'retrieved']

            self._dump_calculation_io(
                parent_path=output_path / io_dump_mapping.outputs,
                link_triples=output_links,
            )

    def _dump_calculation_io(self, parent_path: Path, link_triples: LinkManager | List[LinkTriple]):
        """Small helper function to dump linked input/output nodes of a `CalculationNode`.

        :param parent_path: Parent directory for dumping the linked node contents.
        :param link_triples: List of link triples.
        """

        for link_triple in link_triples:
            link_label = link_triple.link_label

            if not self.flat:
                linked_node_path = parent_path / Path(*link_label.split('__'))
            else:
                # Don't use link_label at all -> But, relative path inside FolderData is retained
                linked_node_path = parent_path

            link_triple.node.base.repository.copy_tree(linked_node_path.resolve())

    def _validate_make_dump_path(self, validate_path: Path, safeguard_file: str = '.aiida_node_metadata.yaml') -> Path:
        """Create default dumping directory for a given process node and return it as absolute path.

        :param validate_path: Path to validate for dumping.
        :param safeguard_file: Dumping-specific file to avoid deleting wrong directory.
            Default: `.aiida_node_metadata.yaml`
        :return: The absolute created dump path.
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
                raise Exception(
                    f"Path `{validate_path}` already exists and doesn't contain safeguard file {safeguard_file}."
                    f' Not removing for safety reasons.'
                )

        # Not included in if-else as to avoid having to repeat the `mkdir` call.
        # `exist_ok=True` as checks implemented above
        validate_path.mkdir(exist_ok=True, parents=True)

        return validate_path.resolve()

    def _generate_calculation_io_mapping(self, io_dump_paths: List[str | Path] | None = None) -> SimpleNamespace:
        """Helper function to generate mapping for entities dumped for each `CalculationNode`.

        This is to avoid exposing AiiDA terminology, like `repository` to the user, while keeping track of which
        entities should be dumped into which directory, and allowing for alternative directory names.

        :param io_dump_paths: Subdirectories created for the `CalculationNode`.
            Default: ['inputs', 'outputs', 'node_inputs', 'node_outputs']
        :return: SimpleNamespace mapping.
        """

        aiida_entities_to_dump = ['repository', 'retrieved', 'inputs', 'outputs']
        default_calculation_io_dump_paths = ['inputs', 'outputs', 'node_inputs', 'node_outputs']
        empty_calculation_io_dump_paths = [''] * 4

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
            LOGGER.info('Flat set to True but `io_dump_paths` provided. These will be used, but `inputs` not nested.')
            return SimpleNamespace(**dict(zip(aiida_entities_to_dump, io_dump_paths)))
        else:
            LOGGER.info(
                'Flat set to False but no `io_dump_paths` provided. These will be used, but `node_inputs` flattened.'
            )
            return SimpleNamespace(**dict(zip(aiida_entities_to_dump, io_dump_paths)))  # type: ignore[arg-type]

    def _dump_node_yaml(
        self,
        process_node: ProcessNode,
        output_path: Path,
        output_filename: str = '.aiida_node_metadata.yaml',
    ) -> None:
        """Dump the selected `ProcessNode` properties, attributes, and extras to a YAML file.

        :param process_node: The `ProcessNode` to dump.
        :param output_path: The path to the directory where the YAML file will be saved.
        :param output_filename: The name of the output YAML file. Defaults to `.aiida_node_metadata.yaml`.
        """

        node_properties = [
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

        user_properties = ('first_name', 'last_name', 'email', 'institution')

        computer_properties = ('label', 'hostname', 'scheduler_type', 'transport_type')

        node_dict = {}
        metadata_dict = {}

        # Add actual node `@property`s to dictionary
        for metadata_property in node_properties:
            metadata_dict[metadata_property] = getattr(process_node, metadata_property)

        node_dict['Node data'] = metadata_dict

        # Add user data
        try:
            node_dbuser = process_node.user
            user_dict = {}
            for user_property in user_properties:
                user_dict[user_property] = getattr(node_dbuser, user_property)
            node_dict['User data'] = user_dict
        except AttributeError:
            pass

        # Add computer data
        try:
            node_dbcomputer = process_node.computer
            computer_dict = {}
            for computer_property in computer_properties:
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
