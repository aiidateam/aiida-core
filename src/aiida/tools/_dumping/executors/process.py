##########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Executor that deals with dumping a single ProcessNode."""

from __future__ import annotations

import contextlib
import os
from enum import Enum, auto
from pathlib import Path
from types import SimpleNamespace
from typing import TYPE_CHECKING, Callable, Optional, Tuple, Union, cast

import yaml

from aiida import orm
from aiida.common import LinkType, timezone
from aiida.common.log import AIIDA_LOGGER
from aiida.orm.utils import LinkTriple
from aiida.tools._dumping.config import DumpMode
from aiida.tools._dumping.tracking import DumpRecord
from aiida.tools._dumping.utils import ORM_TYPE_TO_REGISTRY, DumpPaths, RegistryNameType
from aiida.tools.archive.exceptions import ExportValidationError

if TYPE_CHECKING:
    from aiida.tools._dumping.config import GroupDumpConfig, ProcessDumpConfig, ProfileDumpConfig
    from aiida.tools._dumping.tracking import DumpTracker
    from aiida.tools._dumping.utils import DumpTimes


logger = AIIDA_LOGGER.getChild('tools._dumping.executors.process')

# Type hint for the recursive dump function expected by WorkflowWalker
DumpProcessorType = Callable[[orm.ProcessNode, Path], None]


class NodeDumpAction(Enum):
    """Represents the action determined after checking the log."""

    SKIP = auto()
    SYMLINK = auto()
    DUMP_PRIMARY = auto()
    DUMP_DUPLICATE = auto()
    UPDATE = auto()


class ProcessDumpExecutor:
    """Handles the processing and dumping of individual process nodes"""

    def __init__(
        self,
        config: Union[ProcessDumpConfig, GroupDumpConfig, ProfileDumpConfig],
        dump_paths: DumpPaths,
        dump_tracker: DumpTracker,
        dump_times: DumpTimes,
    ):
        self.config: Union[ProcessDumpConfig, GroupDumpConfig, ProfileDumpConfig] = config
        self.dump_paths: DumpPaths = dump_paths
        self.dump_tracker: DumpTracker = dump_tracker
        self.dump_times: DumpTimes = dump_times

        # Instantiate helper classes
        self.metadata_writer = NodeMetadataWriter(config)
        self.repo_io_dumper = NodeRepoIoDumper(config)
        self.workflow_walker = WorkflowWalker(self.dump)
        self.readme_generator = ReadmeGenerator()

    def dump(
        self,
        process_node: orm.ProcessNode,
        output_path: Path,
    ) -> None:
        """Main entry point to dump a ProcessNode. Determines required action and delegates to execution methods.

        :param process_node: The ``orm.ProcessNode`` to be dumped
        :param output_path: Target output path for node dump
        :return: None
        """

        if not process_node.is_sealed and not self.config.dump_unsealed:
            msg = f'Process {process_node.pk} must be sealed before it can be dumped, or `--dump-unsealed` set to True.'
            raise ExportValidationError(msg)

        if not process_node.pk:
            return

        if self.config.dump_mode == DumpMode.DRY_RUN:
            return

        action, existing_dump_record = self._check_log_and_determine_action(
            process_node=process_node,
            output_path=output_path,
        )

        # Delegate execution based on the determined action
        try:
            if action == NodeDumpAction.DUMP_PRIMARY:
                self._execute_dump_primary(process_node, output_path)
            elif existing_dump_record is not None:
                if action == NodeDumpAction.SKIP:
                    self._execute_skip()
                elif action == NodeDumpAction.SYMLINK:
                    self._execute_symlink(process_node, output_path, existing_dump_record)
                elif action == NodeDumpAction.UPDATE:
                    self._execute_update(process_node, output_path, existing_dump_record)
                elif action == NodeDumpAction.DUMP_DUPLICATE:
                    self._execute_dump_duplicate(process_node, output_path, existing_dump_record)
        except Exception as e:
            self._handle_dump_error(action, process_node, output_path, e)

    def _handle_dump_error(
        self, action: NodeDumpAction, process_node: orm.ProcessNode, output_path: Path, error: Exception
    ):
        """Handle all dump execution errors with appropriate logging and cleanup strategies.

        :param action: Dumping action that was intended to be performed
        :param process_node: The ``orm.ProcessNode`` intended to be dumped
        :param output_path: Dumping target path
        :param error: The orrer that occurred during dumping
        """

        error_type = type(error).__name__
        base_message = f'{error_type} during {action.name} for node PK={process_node.pk}'

        if isinstance(error, PermissionError):
            logger.error(f'{base_message} at {output_path}: Permission denied - {error}', exc_info=True)
            should_cleanup = False  # Don't attempt cleanup if we can't write

        elif isinstance(error, FileNotFoundError):
            logger.error(f'{base_message} at {output_path}: File not found - {error}', exc_info=True)
            should_cleanup = True

        elif isinstance(error, OSError):
            logger.error(f'{base_message} at {output_path}: OS error - {error}', exc_info=True)
            should_cleanup = True

        elif hasattr(error, '__module__') and 'aiida' in error.__module__:
            # AiiDA-specific errors (like ExportValidationError)
            logger.error(f'{base_message}: AiiDA error - {error}', exc_info=True)
            should_cleanup = False  # Validation errors typically don't need cleanup

        else:
            # Unexpected errors
            logger.error(f'{base_message} at {output_path}: Unexpected error - {error}', exc_info=True)
            should_cleanup = True

        # Attempt cleanup if appropriate
        if should_cleanup and action != NodeDumpAction.SKIP:
            try:
                is_primary_attempt = action == NodeDumpAction.DUMP_PRIMARY
                self._cleanup_failed_dump(process_node, output_path, is_primary_attempt)
            except Exception as cleanup_error:
                logger.warning(f'Cleanup failed for node PK={process_node.pk}: {cleanup_error}')

        # Always re-raise the original exception
        # PRCOMMENT: Should I always raise here? Should the full dump fail because of one node dump failure?
        raise  # noqa: PLE0704

    def _check_log_and_determine_action(
        self,
        process_node: orm.ProcessNode,
        output_path: Path,
    ) -> Tuple[NodeDumpAction, Optional[DumpRecord]]:
        """Checks the logger and node status to determine the appropriate dump action.

        :param node: The ``orm.ProcessNode`` to be evaluated
        :param output_path: Dumping target path
        :return: ``NodeDumpAction`` enum instance, and existing ``DumpRecord``, if applicable
        """

        try:
            existing_dump_record = self.dump_tracker.get_entry(process_node.uuid)
        except ValueError:
            return NodeDumpAction.DUMP_PRIMARY, None

        resolved_output_path = output_path.resolve()

        # Case 1: Target path is the SAME as the primary logged path
        if resolved_output_path == existing_dump_record.path.resolve():
            # Check if node mtime is newer than logged dump mtime
            node_mtime = process_node.mtime
            logged_dir_mtime = existing_dump_record.dir_mtime

            needs_update = False
            if logged_dir_mtime is None:
                needs_update = True
            # Ensure comparison is between timezone-aware datetimes
            elif node_mtime.astimezone(timezone.utc) > logged_dir_mtime.astimezone(timezone.utc):
                needs_update = True

            if needs_update:
                return NodeDumpAction.UPDATE, existing_dump_record
            else:
                return NodeDumpAction.SKIP, existing_dump_record

        # Case 2: Target path is DIFFERENT from primary logged path
        is_calc_node = isinstance(process_node, orm.CalculationNode)
        is_sub_process = (
            len(process_node.base.links.get_incoming(link_type=(LinkType.CALL_CALC, LinkType.CALL_WORK)).all()) > 0
        )

        # Option A: Symlink Calculation
        if self.config.symlink_calcs and is_calc_node:
            return NodeDumpAction.SYMLINK, existing_dump_record

        # Option B: Force Duplicate Calculation Dump (if not symlinking)
        elif is_calc_node and is_sub_process and not self.config.only_top_level_calcs:
            return NodeDumpAction.DUMP_DUPLICATE, existing_dump_record

        # Option C: Standard Duplicate Dump (e.g., Workflows, non-symlinked Calcs)
        else:
            return NodeDumpAction.DUMP_DUPLICATE, existing_dump_record

    def _execute_dump_primary(self, process_node: orm.ProcessNode, output_path: Path):
        """Action: Perform a full dump as the primary location.

        :param node: The ``orm.ProcessNode`` to be processed
        :param output_path: Dumping target path
        """

        dump_record = None

        # Prepare directory
        self.dump_paths._prepare_directory(path_to_prepare=output_path, is_leaf_node_dir=False)

        # Create new log entry
        dump_record = DumpRecord(path=output_path.resolve())
        registry_key = ORM_TYPE_TO_REGISTRY[type(process_node)]
        self.dump_tracker.registries[cast(RegistryNameType, registry_key)].add_entry(process_node.uuid, dump_record)

        # Dump content
        self._dump_node_content(process_node, output_path)

        # Calculate and update stats for the new log entry
        dump_record.update_stats(path=output_path)

    def _execute_skip(self) -> None:
        """Action: Skip dumping this node."""
        pass

    def _execute_symlink(
        self, process_node: orm.ProcessNode, output_path: Path, existing_dump_record: DumpRecord
    ) -> None:
        """Action: Create a relative symlink to the primary dump location.

        :param node: The ``orm.ProcessNode`` to be processed
        :param output_path: Dumping target path
        :param existing_dump_record: ``DumpRecord`` retrieved from ``DumpTracker``
        :return: None
        """

        # Avoid creating symlink if target already exists (idempotency)
        if output_path.exists() or output_path.is_symlink():
            logger.warning(f'Target path {output_path.name} already exists. Skipping symlink creation.')
            # Ensure log entry reflects this link target even if skipped
            if output_path.resolve() not in {p.resolve() for p in existing_dump_record.symlinks if p.exists()}:
                try:
                    existing_dump_record.add_symlink(output_path.resolve())
                except OSError as e:
                    logger.error(f'Could not resolve path {output_path} to add to symlinks log: {e}')
                    raise
            return  # Skip actual symlink creation

        source_path = existing_dump_record.path  # Absolute path to the original dump dir
        if not source_path.exists():
            logger.error(f'Source path {source_path} for node {process_node.pk} does not exist. Cannot symlink.')
            # No cleanup needed here, just log the error
            return

        link_location_dir = output_path.parent
        link_location_dir.mkdir(parents=True, exist_ok=True)
        relative_src_path = os.path.relpath(source_path, start=link_location_dir)

        os.symlink(relative_src_path, output_path, target_is_directory=True)

        # Add this new symlink location to the log entry
        existing_dump_record.add_symlink(output_path.resolve())

    def _execute_update(self, process_node: orm.ProcessNode, output_path: Path, existing_dump_record: DumpRecord):
        """Action: Clean existing directory and perform a full dump.

        :param node: The ``orm.ProcessNode`` to be processed
        :param output_path: Dumping target path
        :param existing_dump_record: ``DumpRecord`` retrieved from ``DumpTracker``
        """

        # Clean existing directory
        DumpPaths._safe_delete_directory(path=output_path)

        # Prepare directory again
        self.dump_paths._prepare_directory(path_to_prepare=output_path)

        # Dump content
        self._dump_node_content(process_node, output_path)

        # Update stats on the existing log entry using the primary path
        existing_dump_record.update_stats(path=output_path)

    def _execute_dump_duplicate(
        self, process_node: orm.ProcessNode, output_path: Path, existing_dump_record: DumpRecord
    ):
        """Action: Perform a full dump at a secondary location.

        :param node: The ``orm.ProcessNode`` to be processed
        :param output_path: Dumping target path
        :param existing_dump_record: ``DumpRecord`` retrieved from ``DumpTracker``
        """

        # Prepare directory
        self.dump_paths._prepare_directory(path_to_prepare=output_path)

        # Add path to duplicates list in existing log entry
        existing_dump_record.add_duplicate(output_path.resolve())

        # Dump content
        self._dump_node_content(process_node, output_path)

    def _dump_node_content(
        self,
        process_node: orm.ProcessNode,
        output_path: Path,
    ):
        """Dumps the actual content (metadata, repo, children).

        :param node: The ``orm.ProcessNode`` to be processed
        :param output_path: Dumping target path
        """

        # Write Metadata
        self.metadata_writer._write(process_node, output_path)

        # Ensure top-level safeguard exists
        (output_path / DumpPaths.SAFEGUARD_FILE_NAME).touch(exist_ok=True)

        # Dump Repo/IO or Recurse Children
        if isinstance(process_node, orm.CalculationNode):
            self.repo_io_dumper._dump_calculation_content(process_node, output_path)
        elif isinstance(process_node, orm.WorkflowNode):
            self.workflow_walker._dump_children(process_node, output_path)

    def _cleanup_failed_dump(
        self,
        process_node: orm.ProcessNode,
        output_path: Path,
        is_primary_dump: bool,
    ):
        """Cleans up directory and potentially log entry on failure.

        :param node: The ``orm.ProcessNode`` to be processed
        :param output_path: Dumping target path
        :param is_primary_dump: If first time the node is being dumped: determines cleanup behavior.
        """

        logger.warning(f'Attempting cleanup for failed dump of node {process_node.pk} at {output_path.name}')
        DumpPaths._safe_delete_directory(path=output_path)

        if is_primary_dump:
            registry_key = ORM_TYPE_TO_REGISTRY[type(process_node)]
            node_registry = self.dump_tracker.registries[registry_key]
            node_registry.del_entry(process_node.uuid)

    @staticmethod
    def generate_child_node_label(index: int, link_triple: LinkTriple, append_pk: bool = True) -> str:
        """Generate directory label for child nodes during recursion.

        :param index: Index in the iteration through the child processes of a workflow
        :param link_triple: As obtained from the outgoing links of the parent process
        :param append_pk: Should append the node PK to the label, defaults to True
        :return: Human-readable label for the child process node, to be used as directory name
        """

        node = link_triple.node
        link_label = link_triple.link_label

        # Generate directories with naming scheme akin to `verdi process status`
        label_list = [f'{index:02d}', link_label]

        # NOTE: Could also use node.label here, similar to main ProcessNode output dumping directory
        try:
            process_label = node.process_label
            if process_label is not None and process_label != link_label:
                label_list += [process_label]

        except AttributeError:
            process_type = node.process_type
            if process_type is not None and process_type != link_label:
                label_list += [process_type]

        if append_pk:
            label_list += [str(node.pk)]

        node_label = '-'.join(label_list)
        node_label = node_label.replace('CALL-', '')
        return node_label.replace('None-', '')


class NodeMetadataWriter:
    """Handles writing the aiida_node_metadata.yaml file."""

    def __init__(self, config: Union[ProcessDumpConfig, GroupDumpConfig, ProfileDumpConfig]):
        self.config: Union[ProcessDumpConfig, GroupDumpConfig, ProfileDumpConfig] = config

    def _write(
        self,
        process_node: orm.ProcessNode,
        output_path: Path,
        output_filename: str = 'aiida_node_metadata.yaml',
    ) -> None:
        """Dump the selected ProcessNode properties, attributes, and extras to a YAML file.

        :param process_node: The ``orm.ProcessNode`` to be processed
        :param output_path: Dumping output path for the given node
        :param output_filename: Output filename for node metadata, defaults to 'aiida_node_metadata.yaml'
        """

        node_properties = (
            'label',
            'description',
            'pk',
            'uuid',
            'ctime',
            'mtime',
            'node_type',
            'process_type',
            'is_finished_ok',
        )
        user_properties = ('first_name', 'last_name', 'email', 'institution')
        computer_properties = ('label', 'hostname', 'scheduler_type', 'transport_type')

        metadata_dict = {prop: getattr(process_node, prop, None) for prop in node_properties}
        node_dict = {'Node data': metadata_dict}

        with contextlib.suppress(AttributeError):
            node_dbuser = process_node.user
            user_dict = {prop: getattr(node_dbuser, prop, None) for prop in user_properties}
            node_dict['User data'] = user_dict

        with contextlib.suppress(AttributeError):
            node_dbcomputer = process_node.computer
            if node_dbcomputer:  # Check if computer is assigned
                computer_dict = {prop: getattr(node_dbcomputer, prop, None) for prop in computer_properties}
                node_dict['Computer data'] = computer_dict

        if self.config.include_attributes:
            node_attributes = process_node.base.attributes.all
            if node_attributes:
                node_dict['Node attributes'] = node_attributes

        if self.config.include_extras:
            node_extras = process_node.base.extras.all
            if node_extras:
                node_dict['Node extras'] = node_extras

        output_file = output_path / output_filename
        output_file.write_text(
            yaml.dump(
                node_dict,
                sort_keys=False,
                default_flow_style=False,
                indent=2,
                width=100,
                allow_unicode=True,
                explicit_start=True,
            ),
            encoding='utf-8',
        )


class NodeRepoIoDumper:
    """Handles dumping repository contents and linked I/O Data nodes."""

    def __init__(self, config: Union[ProcessDumpConfig, GroupDumpConfig, ProfileDumpConfig]):
        self.config: Union[ProcessDumpConfig, GroupDumpConfig, ProfileDumpConfig] = config

    def _dump_calculation_content(self, calculation_node: orm.CalculationNode, output_path: Path) -> None:
        """Dump repository and I/O file contents for a CalculationNode.

        :param calculation_node: The ``orm.CalculationNode`` for which the contents should be dumped
        :param output_path: The dumping output path
        """

        io_dump_mapping = self._generate_calculation_io_mapping(flat=self.config.flat)

        # Dump the main repository contents
        repo_target = output_path / io_dump_mapping.repository
        repo_target.mkdir(parents=True, exist_ok=True)

        calculation_node.base.repository.copy_tree(repo_target)

        # Dump the repository contents of `outputs.retrieved` if it exists
        if hasattr(calculation_node.outputs, 'retrieved'):
            if calculation_node.outputs.retrieved is not None:
                retrieved_target = output_path / io_dump_mapping.retrieved
                retrieved_target.mkdir(parents=True, exist_ok=True)
                calculation_node.outputs.retrieved.base.repository.copy_tree(retrieved_target)

        # Dump the node_inputs (linked Data nodes)
        if self.config.include_inputs:
            input_links = calculation_node.base.links.get_incoming(link_type=LinkType.INPUT_CALC).all()
            if input_links:
                input_path = output_path / io_dump_mapping.inputs
                self._dump_calculation_io_files(
                    parent_path=input_path,
                    link_triples=input_links,
                )

        # Dump the node_outputs (created Data nodes, excluding 'retrieved')
        if self.config.include_outputs:
            output_links = calculation_node.base.links.get_outgoing(link_type=LinkType.CREATE).all()
            output_links_filtered = [link for link in output_links if link.link_label != 'retrieved']
            # NOTE: Expand this here for additional types in the future
            has_dumpable_output = any(
                isinstance(link.node, (orm.SinglefileData, orm.FolderData)) for link in output_links_filtered
            )
            if output_links_filtered and has_dumpable_output:
                output_path_target = output_path / io_dump_mapping.outputs
                output_path_target.mkdir(parents=True, exist_ok=True)
                self._dump_calculation_io_files(
                    parent_path=output_path_target,
                    link_triples=output_links_filtered,
                )

    def _dump_calculation_io_files(
        self,
        parent_path: Path,
        link_triples: list[LinkTriple],
    ):
        """Helper to dump linked input/output Data nodes.

        :param parent_path: Dumping parent path of the ``orm.CalculationNode``
        :param link_triples: List of ``LinkTriples`` (incoming, outgoing)
        """

        for link_triple in link_triples:
            node = link_triple.node
            link_label = link_triple.link_label
            if not self.config.flat:
                relative_parts = link_label.split('__')
                linked_node_path = parent_path.joinpath(*relative_parts)
            else:
                # Dump content directly into parent_path,
                # Preserve repository-internal file hierarchy
                linked_node_path = parent_path

            if node.base.repository.list_object_names():
                linked_node_path.parent.mkdir(parents=True, exist_ok=True)
                node.base.repository.copy_tree(linked_node_path)

    @staticmethod
    def _generate_calculation_io_mapping(flat: bool = False) -> SimpleNamespace:
        """Helper to map internal names to directory names for CalculationNode I/O.

        :param flat: Flat dumping, with repository-internal structure reserved, or create subdirectories based on
            entities being dumped.
        """

        aiida_entities = ['repository', 'retrieved', 'inputs', 'outputs']
        default_dirs = ['inputs', 'outputs', 'node_inputs', 'node_outputs']

        if flat:
            # Empty string means dump into the parent directory itself
            mapping = {entity: '' for entity in aiida_entities}
        else:
            mapping = dict(zip(aiida_entities, default_dirs))

        return SimpleNamespace(**mapping)


class WorkflowWalker:
    """Handles traversing WorkflowNode children and triggering their dump."""

    def __init__(self, dump_processor: DumpProcessorType):
        """
        Initialize the WorkflowWalker.

        :param dump_processor: A callable that takes a node and a target path to dump it.
        """
        self.dump_processor = dump_processor

    def _dump_children(self, workflow_node: orm.WorkflowNode, output_path: Path) -> None:
        """Find and recursively dump children of a WorkflowNode.

        :param workflow_node: ``orm.WorkflowNode`` that should be recursively traversed
            (could be top-level or sub-workflow)
        :param output_path: Dumping target output path
        """
        called_links = workflow_node.base.links.get_outgoing(link_type=(LinkType.CALL_CALC, LinkType.CALL_WORK)).all()
        # Sort by `ctime`
        called_links = sorted(called_links, key=lambda link_triple: link_triple.node.ctime)

        for index, link_triple in enumerate(called_links, start=1):
            child_node = link_triple.node
            assert isinstance(child_node, orm.ProcessNode)
            # Use static method from ProcessDumpExecutor to generate label consistently
            child_label = ProcessDumpExecutor.generate_child_node_label(index=index, link_triple=link_triple)
            child_output_path = output_path / child_label
            # Call the provided dump_processor function for the child
            self.dump_processor(
                child_node,
                child_output_path,
            )


class ReadmeGenerator:
    """Handles generating README.md files for process nodes."""

    def _generate(self, process_node: orm.ProcessNode, output_path: Path) -> None:
        """Generate README.md file in the specified output path.

        :param process_node: The top-level ``orm.ProcessNode`` for which the README file should be generated
        :param output_path: Target top-level output path
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
            # AiiDA Process Dump: {process_node.process_label or process_node.process_type} <{pk}>

            This directory contains files related to the AiiDA process node {pk}.
            - **UUID:** {process_node.uuid}
            - **Type:** {process_node.node_type}

            Sub-directories (if present) represent called calculations or workflows, ordered by creation time.
            File/directory structure within a calculation node:
            - `inputs/`: Contains scheduler submission script (`_aiidasubmit.sh`), stdin file (`aiida.in`), and internal
            AiiDA info (`.aiida/`).
            - `outputs/`: Contains files retrieved by the parser (e.g., `aiida.out`, `_scheduler-stdout.txt`,
            `_scheduler-stderr.txt`).
            - `node_inputs/`: Contains repositories of input data nodes linked via `INPUT_CALC`.
            - `node_outputs/`: Contains repositories of output data nodes linked via `CREATE` (excluding `retrieved`).
            - `aiida_node_metadata.yaml`: Human-readable metadata, attributes, and extras of this node.
            """
        )

        # Add status, report, show info
        _readme_string += (
            f'\n## Process Status (`verdi process status {pk}`)\n\n```\n{format_call_graph(process_node)}\n```\n'
        )

        if isinstance(process_node, orm.CalcJobNode):
            report = get_calcjob_report(process_node)
        elif isinstance(process_node, orm.WorkChainNode):
            report = get_workchain_report(node=process_node, levelname='REPORT', indent_size=2, max_depth=None)
        elif isinstance(process_node, (orm.CalcFunctionNode, orm.WorkFunctionNode)):
            report = get_process_function_report(process_node)
        else:
            report = 'N/A'
        _readme_string += f'\n## Process Report (`verdi process report {pk}`)\n\n```\n{report}\n```\n'

        _readme_string += (
            f'\n## Node Info (`verdi node show {process_node.uuid}`)\n\n```\n{get_node_info(process_node)}\n```\n'
        )

        (output_path / 'README.md').write_text(_readme_string, encoding='utf-8')
