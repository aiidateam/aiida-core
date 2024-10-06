###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Functionality for dumping of orm.ProcessNodes."""

from __future__ import annotations

import contextlib
import logging
import os
from pathlib import Path
from types import SimpleNamespace
from typing import List

import yaml

from aiida import orm
from aiida.cmdline.params.types import FileOrUrl
from aiida.common import LinkType
from aiida.common.exceptions import NotExistentAttributeError
from aiida.tools.dumping.data import DataDumper
from aiida.tools.dumping.rich import DEFAULT_CORE_EXPORT_MAPPING, RichParser
from aiida.tools.dumping.utils import validate_make_dump_path

logger = logging.getLogger(__name__)

SAFEGUARD_FILE = '.aiida_node_metadata.yaml'


class ProcessDumper:
    def __init__(
        self,
        *args,
        overwrite: bool = False,
        flat: bool = False,
        include_inputs: bool = True,
        include_outputs: bool = False,
        include_attributes: bool = True,
        include_extras: bool = True,
        also_raw: bool = False,
        also_rich: bool = False,
        rich_options: str = '',
        rich_config_file: FileOrUrl | None = None,
        rich_dump_all: bool = True,
        data_dumper: DataDumper | None = None,
        **kwargs,
    ) -> None:
        self.args = args
        self.overwrite = overwrite
        self.flat = flat
        self.include_inputs = include_inputs
        self.include_outputs = include_outputs
        self.include_attributes = include_attributes
        self.include_extras = include_extras
        self.also_raw = also_raw
        self.also_rich = also_rich
        self.rich_options = rich_options
        self.rich_config_file = rich_config_file
        self.rich_dump_all = rich_dump_all
        self.data_dumper = data_dumper
        self.kwargs = kwargs

    @staticmethod
    def _generate_default_dump_path(process_node: orm.ProcessNode, prefix: str | None = None) -> Path:
        """Simple helper function to generate the default parent-dumping directory if none given.

        This function is not called for the recursive sub-calls of `_dump_calculation` as it just creates the default
        parent folder for the dumping, if no name is given.

        :param process_node: The `orm.ProcessNode` for which the directory is created.
        :return: The absolute default parent dump path.
        """

        pk = process_node.pk
        try:
            return Path('-'.join(filter(None, [prefix, process_node.process_label, str(pk)])))
        except AttributeError:
            # This case came up during testing, not sure how relevant it actually is
            return Path('-'.join(filter(None, [prefix, process_node.process_type, pk])))

    @staticmethod
    def _generate_readme(process_node: orm.ProcessNode, output_path: Path) -> None:
        """Generate README.md file in main dumping directory.

        :param process_node: `orm.CalculationNode` or `orm.WorkflowNode`.
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
        if isinstance(process_node, orm.CalcJobNode):
            process_report = get_calcjob_report(process_node)
        elif isinstance(process_node, orm.WorkChainNode):
            process_report = get_workchain_report(process_node, levelname='REPORT', indent_size=2, max_depth=None)
        elif isinstance(process_node, (orm.CalcFunctionNode, orm.WorkFunctionNode)):
            process_report = get_process_function_report(process_node)
        else:
            process_report = f'Nothing to show for node type {process_node.__class__}'

        _readme_string += f'\n\n\nOutput of `verdi process report {pk}`:\n\n```shell\n{process_report}\n```'

        # `verdi process show`?
        process_show = get_node_info(node=process_node)
        _readme_string += f'\n\n\nOutput of `verdi process show {pk}`:\n\n```shell\n{process_show}\n```'

        (output_path / 'README.md').write_text(_readme_string)

    @staticmethod
    def _generate_child_node_label(index: int, link_triple: orm.LinkTriple) -> str:
        """Small helper function to generate and clean directory label for child nodes during recursion.

        :param index: Index assigned to step at current level of recursion.
        :param link_triple: `orm.LinkTriple` of `orm.ProcessNode` explored during recursion.
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
        return node_label.replace('None-', '')

    def dump(
        self,
        process_node: orm.ProcessNode,
        output_path: Path | None,
        io_dump_paths: List[str | Path] | None = None,
        *args,
        **kwargs,
    ) -> Path:
        """Dumps all data involved in a `orm.ProcessNode`, including its outgoing links.

        Note that if an outgoing link is a `orm.WorkflowNode`, the function recursively calls itself, while files are
        only actually created when a `orm.CalculationNode` is reached.

        :param process_node: The parent `orm.ProcessNode` node to be dumped.
        :param output_path: The output path where the directory tree will be created.
        :param io_dump_paths: Subdirectories created for each `orm.CalculationNode`.
            Default: ['inputs', 'outputs', 'node_inputs', 'node_outputs']
        """

        if not process_node.is_finished:
            self.incremental = True
            # Could also raise an exception here
            # raise NotImplementedError("Node isn't finished and incremental dumping not supported yet.")
            logger.report("Node isn't finished and incremental dumping not supported yet.")
            return

        # This here is mainly for `include_attributes` and `include_extras`.
        # I don't want to include them in the general class `__init__`, as they don't really fit there.
        # But the `_dump_node_yaml` function is private, so it's never called outside by the user.
        # Setting the class attributes here dynamically is probably not a good solution, but it works for now.
        for key, value in kwargs.items():
            setattr(self, key, value)

        if output_path is None:
            output_path = self._generate_default_dump_path(process_node=process_node)

        validate_make_dump_path(
            overwrite=self.overwrite, path_to_validate=output_path, logger=logger, safeguard_file=SAFEGUARD_FILE
        )

        if isinstance(process_node, orm.CalculationNode):
            self._dump_calculation(
                calculation_node=process_node,
                output_path=output_path,
                io_dump_paths=io_dump_paths,
            )

        elif isinstance(process_node, orm.WorkflowNode):
            self._dump_workflow(
                workflow_node=process_node,
                output_path=output_path,
                io_dump_paths=io_dump_paths,
            )

        self._generate_readme(process_node=process_node, output_path=output_path)

        return output_path

    def _dump_workflow(
        self,
        workflow_node: orm.WorkflowNode,
        output_path: Path,
        io_dump_paths: List[str | Path] | None = None,
        link_calculations: bool = False,
        link_calculations_dir: str | None = None,
    ) -> None:
        """Recursive function to traverse a `orm.WorkflowNode` and dump its `orm.CalculationNode` s.

        :param workflow_node: `orm.WorkflowNode` to be traversed. Will be updated during recursion.
        :param output_path: Dumping parent directory. Will be updated during recursion.
        :param io_dump_paths: Custom subdirectories for `orm.CalculationNode` s, defaults to None
        """

        validate_make_dump_path(
            path_to_validate=output_path, overwrite=self.overwrite, logger=logger, safeguard_file=SAFEGUARD_FILE
        )
        self._dump_node_yaml(process_node=workflow_node, output_path=output_path)

        called_links = workflow_node.base.links.get_outgoing(link_type=(LinkType.CALL_CALC, LinkType.CALL_WORK)).all()
        called_links = sorted(called_links, key=lambda link_triple: link_triple.node.ctime)

        for index, link_triple in enumerate(called_links, start=1):
            child_node = link_triple.node
            child_label = self._generate_child_node_label(index=index, link_triple=link_triple)
            child_output_path = output_path.resolve() / child_label

            # Recursive function call for `orm.WorkflowNode`
            if isinstance(child_node, orm.WorkflowNode):
                self._dump_workflow(
                    workflow_node=child_node,
                    output_path=child_output_path,
                    io_dump_paths=io_dump_paths,
                    # TODO: Always need to pass this stuff through due to the recursive nature of the function call...
                    # TODO: Maybe one can make a separate method that only does the linking
                    link_calculations=link_calculations,
                    link_calculations_dir=link_calculations_dir,
                )

            # Once a `orm.CalculationNode` as child reached, dump it
            elif isinstance(child_node, orm.CalculationNode):
                if not link_calculations:
                    self._dump_calculation(
                        calculation_node=child_node,
                        output_path=child_output_path,
                        io_dump_paths=io_dump_paths,
                    )
                else:
                    os.symlink(link_calculations_dir / child_node.uuid, child_output_path)

    def _dump_calculation(
        self,
        calculation_node: orm.CalculationNode,
        output_path: Path,
        io_dump_paths: List[str | Path] | None = None,
    ) -> None:
        """Dump the contents of a `orm.CalculationNode` to a specified output path.

        :param calculation_node: The `orm.CalculationNode` to be dumped.
        :param output_path: The path where the files will be dumped.
        :param io_dump_paths: Subdirectories created for the `orm.CalculationNode`.
            Default: ['inputs', 'outputs', 'node_inputs', 'node_outputs']
        """

        validate_make_dump_path(
            overwrite=self.overwrite, path_to_validate=output_path, logger=logger, safeguard_file=SAFEGUARD_FILE
        )
        self._dump_node_yaml(process_node=calculation_node, output_path=output_path)

        io_dump_mapping = self._generate_calculation_io_mapping(io_dump_paths=io_dump_paths)

        # Dump the repository contents of the node
        calculation_node_repo = calculation_node.base.repository
        calculation_node_repo.copy_tree(output_path.resolve() / io_dump_mapping.repository)

        # Dump the repository contents of `outputs.retrieved`
        with contextlib.suppress(NotExistentAttributeError):
            calculation_node.outputs.retrieved.base.repository.copy_tree(
                output_path.resolve() / io_dump_mapping.retrieved
            )

        if self.also_raw:
            # TODO: Replace with attached self.data_dumper attribute
            DataDumper().dump_raw(data_node=calculation_node, output_path=output_path)

        # Dump the node_inputs
        if self.include_inputs:
            input_links = calculation_node.base.links.get_incoming(link_type=LinkType.INPUT_CALC)
            # Need to create the path before, otherwise getting Exception
            input_path = output_path / io_dump_mapping.inputs
            input_path.mkdir(parents=True, exist_ok=True)

            self._dump_calculation_io_files(parent_path=output_path / io_dump_mapping.inputs, link_triples=input_links)

            if self.also_raw:
                self._dump_calculation_io_files_raw(
                    output_path=output_path / io_dump_mapping.inputs, link_triples=input_links
                )

            if self.also_rich:
                self._dump_calculation_io_files_rich(
                    output_path=output_path / io_dump_mapping.inputs, link_triples=input_links
                )

        # Dump the node_outputs apart from `retrieved`
        if self.include_outputs:
            output_links = list(calculation_node.base.links.get_outgoing(link_type=LinkType.CREATE))
            output_links = [output_link for output_link in output_links if output_link.link_label != 'retrieved']
            node_output_path = output_path / io_dump_mapping.outputs
            node_output_path.mkdir(parents=True, exist_ok=True)

            self._dump_calculation_io_files(
                parent_path=output_path / io_dump_mapping.outputs,
                link_triples=output_links,
            )

            if self.also_raw:
                self._dump_calculation_io_files_raw(
                    output_path=output_path / io_dump_mapping.outputs,
                    link_triples=output_links,
                )

            if self.also_rich:
                self._dump_calculation_io_files_rich(
                    output_path=output_path / io_dump_mapping.outputs,
                    link_triples=output_links,
                )

    def _dump_calculation_io_files(
        self,
        parent_path: Path,
        link_triples: orm.LinkManager | List[orm.LinkTriple],
    ):
        """Small helper function to dump linked input/output nodes of a `orm.CalculationNode`.

        :param parent_path: Parent directory for dumping the linked node contents.
        :param link_triples: List of link triples.
        """

        # Dump the actual files of each node, e.g. `.npy` files for arrays
        for link_triple in link_triples:
            link_label = link_triple.link_label

            if not self.flat:
                linked_node_path = parent_path / Path(*link_label.split('__'))
            else:
                # Don't use link_label at all -> But, relative path inside FolderData is retained
                linked_node_path = parent_path

            link_triple.node.base.repository.copy_tree(linked_node_path.resolve())

    def _dump_calculation_io_files_raw(
        self,
        output_path: Path,
        link_triples: orm.LinkManager | List[orm.LinkTriple],
    ):
        """Small helper function to dump linked input/output nodes of a `orm.CalculationNode`.

        :param parent_path: Parent directory for dumping the linked node contents.
        :param link_triples: List of link triples.
        """

        output_path /= 'raw'

        for link_triple in link_triples:
            link_label = link_triple.link_label
            data_node = link_triple.node

            # linked_node_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.mkdir(parents=True, exist_ok=True)

            # Then dump the node attributes for each node
            output_fname = DataDumper.generate_output_fname_raw(prefix=link_label, data_node=data_node)
            output_fname = output_fname.replace('__', '_')

            DataDumper().dump_raw(data_node=data_node, output_path=output_path, output_fname=output_fname)

    def _dump_calculation_io_files_rich(
        self,
        output_path: Path,
        link_triples: orm.LinkManager | List[orm.LinkTriple],
    ):
        """Small helper function to dump linked input/output nodes of a `orm.CalculationNode`.

        :param parent_path: Parent directory for dumping the linked node contents.
        :param link_triples: List of link triples.
        """

        output_path /= 'rich'

        # Set up the rich parsing functions

        # Extend (at least the keys) by the dynamic entry points

        if self.rich_options is not None:
            rich_options_dict = RichParser.from_cli(rich_options=self.rich_options)

        elif self.rich_config_file is not None:
            rich_options_dict = RichParser.from_config(rich_options=self.rich_config_file)

        else:
            rich_options_dict = DEFAULT_CORE_EXPORT_MAPPING

        for link_triple in link_triples:
            link_label = link_triple.link_label
            data_node = link_triple.node

            node = link_triple.node
            node_entry_point = node.entry_point
            node_entry_point_name = node_entry_point.name

            # TODO: Somehow obtain sensible filenames -> Should this be done here, or by the export function that is
            # TODO: possibly written by the plugin developer
            if node_entry_point_name.startswith('core'):
                # Obtain settings from the export dict
                # TODO: -> This might break when plugin is missing
                try:
                    exporter = rich_options_dict[node_entry_point_name]['exporter']
                    fileformat = rich_options_dict[node_entry_point_name]['export_format']
                    output_fname = DataDumper.generate_output_fname_rich(
                        prefix=link_label, data_node=data_node, fileformat=fileformat
                    )
                    output_fname = output_fname.replace('__', '_')
                except:
                    raise

                # No exporter set
                if exporter is None:
                    continue

                # Only create subdirectory if `Data` node has an exporter
                output_path.mkdir(parents=True, exist_ok=True)

                DataDumper().dump_rich_core(
                    node,
                    rich_options_dict=rich_options_dict,
                    output_path=output_path,
                    output_fname=output_fname,
                )

    def _generate_calculation_io_mapping(self, io_dump_paths: List[str | Path] | None = None) -> SimpleNamespace:
        """Helper function to generate mapping for entities dumped for each `orm.CalculationNode`.

        This is to avoid exposing AiiDA terminology, like `repository` to the user, while keeping track of which
        entities should be dumped into which directory, and allowing for alternative directory names.

        :param io_dump_paths: Subdirectories created for the `orm.CalculationNode`.
            Default: ['inputs', 'outputs', 'node_inputs', 'node_outputs']
        :return: SimpleNamespace mapping.
        """

        aiida_entities_to_dump = ['repository', 'retrieved', 'inputs', 'outputs']
        default_calculation_io_dump_paths = ['inputs', 'outputs', 'node_inputs', 'node_outputs']
        if self.flat and io_dump_paths is None:
            logger.info(
                'Flat set to True and no `io_dump_paths`. Dumping in a flat directory, files might be overwritten.'
            )
            empty_calculation_io_dump_paths = [''] * 4

            return SimpleNamespace(**dict(zip(aiida_entities_to_dump, empty_calculation_io_dump_paths)))

        elif not self.flat and io_dump_paths is None:
            logger.info(
                'Flat set to False but no `io_dump_paths` provided. '
                + f'Will use the defaults {default_calculation_io_dump_paths}.'
            )
            return SimpleNamespace(**dict(zip(aiida_entities_to_dump, default_calculation_io_dump_paths)))

        elif self.flat:
            logger.info('Flat set to True but `io_dump_paths` provided. These will be used, but `inputs` not nested.')
            return SimpleNamespace(**dict(zip(aiida_entities_to_dump, io_dump_paths)))
        else:
            logger.info(
                'Flat set to False but no `io_dump_paths` provided. These will be used, but `node_inputs` flattened.'
            )
            return SimpleNamespace(**dict(zip(aiida_entities_to_dump, io_dump_paths)))  # type: ignore[arg-type]

    def _dump_node_yaml(
        self,
        process_node: orm.ProcessNode,
        output_path: Path,
        output_filename: str = '.aiida_node_metadata.yaml',
        include_attributes: bool = True,
        include_extras: bool = True,
    ) -> None:
        """Dump the selected `orm.ProcessNode` properties, attributes, and extras to a YAML file.

        :param process_node: The `orm.ProcessNode` to dump.
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

        metadata_dict = {
            metadata_property: getattr(process_node, metadata_property) for metadata_property in node_properties
        }
        node_dict = {'Node data': metadata_dict}
        # Add user data
        with contextlib.suppress(AttributeError):
            node_dbuser = process_node.user
            user_dict = {user_property: getattr(node_dbuser, user_property) for user_property in user_properties}
            node_dict['User data'] = user_dict

        # Add computer data
        with contextlib.suppress(AttributeError):
            node_dbcomputer = process_node.computer
            computer_dict = {
                computer_property: getattr(node_dbcomputer, computer_property)
                for computer_property in computer_properties
            }
            node_dict['Computer data'] = computer_dict
        # Add node attributes
        if include_attributes:
            node_attributes = process_node.base.attributes.all
            node_dict['Node attributes'] = node_attributes

        if include_extras:
            if node_extras := process_node.base.extras.all:
                node_dict['Node extras'] = node_extras

        output_file = output_path.resolve() / output_filename
        with open(output_file, 'w') as handle:
            yaml.dump(node_dict, handle, sort_keys=False)
