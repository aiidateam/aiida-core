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
from typing import TYPE_CHECKING, Callable, Optional, Tuple, cast

import yaml

from aiida import orm
from aiida.common import LinkType, timezone
from aiida.common.log import AIIDA_LOGGER
from aiida.orm.utils import LinkTriple
from aiida.tools.archive.exceptions import ExportValidationError
from aiida.tools.dumping.config import DumpConfig
from aiida.tools.dumping.tracking import DumpRecord
from aiida.tools.dumping.utils import ORM_TYPE_TO_REGISTRY, DumpPaths, RegistryNameType

if TYPE_CHECKING:
    from aiida.tools.dumping.tracking import DumpTracker
    from aiida.tools.dumping.utils import DumpTimes

__all__ = ('NodeMetadataWriter', 'NodeRepoIoDumper', 'ProcessDumpExecutor', 'ReadmeGenerator', 'WorkflowWalker')

logger = AIIDA_LOGGER.getChild('tools.dumping.executors.process')

# Type hint for the recursive dump function expected by WorkflowWalker
DumpProcessorType = Callable[[orm.ProcessNode, Path], None]


# TODO: end-user should specify a few actions what to do when duplicate entities are encountered
# TODO: This should be general `--handle-duplicates` or sthg
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
        config: DumpConfig,
        dump_paths: DumpPaths,
        dump_tracker: DumpTracker,
        dump_times: DumpTimes,
    ):
        self.config: DumpConfig = config
        self.dump_paths: DumpPaths = dump_paths
        self.dump_tracker: DumpTracker = dump_tracker
        self.dump_times: DumpTimes = dump_times

        # Instantiate helper classes
        self.metadata_writer = NodeMetadataWriter(config)
        self.repo_io_dumper = NodeRepoIoDumper(config)
        # Pass the bound method self._dump_process_recursive_entry for recursion
        self.workflow_walker = WorkflowWalker(self.dump)
        self.readme_generator = ReadmeGenerator()

    def dump(
        self,
        process_node: orm.ProcessNode,
        target_path: Path | None = None,
    ):
        """
        Main entry point to dump a single ProcessNode.
        Determines the required action and delegates to execution methods.
        """
        if not target_path:
            raise Exception

        if not self._validate_node_for_dump(process_node):
            return  # Validation failed, logged inside helper

        action, existing_dump_record = self._check_log_and_determine_action(
            node=process_node,
            target_path=target_path,
        )

        # Delegate execution based on the determined action
        try:
            if action == NodeDumpAction.DUMP_PRIMARY:
                self._execute_dump_primary(process_node, target_path)
            elif action == NodeDumpAction.SKIP:
                self._execute_skip()
            elif existing_dump_record is not None:
                if action == NodeDumpAction.SYMLINK:
                    self._execute_symlink(process_node, target_path, existing_dump_record)
                elif action == NodeDumpAction.UPDATE:
                    self._execute_update(process_node, target_path, existing_dump_record)
                elif action == NodeDumpAction.DUMP_DUPLICATE:
                    self._execute_dump_duplicate(process_node, target_path, existing_dump_record)
        except Exception as e:
            # Catch errors during execution phase
            logger.error(
                f'Unhandled exception during execution of action {action.name} '
                f'for node PK={process_node.pk} at {target_path}: {e}',
                exc_info=True,
            )
            # Decide on cleanup: only cleanup primary if primary failed
            is_primary_attempt = action == NodeDumpAction.DUMP_PRIMARY
            self._cleanup_failed_dump(process_node, target_path, is_primary_attempt)

    def _check_log_and_determine_action(
        self,
        node: orm.ProcessNode,
        target_path: Path,
    ) -> Tuple[NodeDumpAction, Optional[DumpRecord]]:
        """
        Checks the logger and node status to determine the appropriate dump action.
        This method should NOT have side effects like creating files/dirs or modifying logs.
        """
        existing_dump_record = self.dump_tracker.get_entry(node.uuid)

        if not existing_dump_record:
            return NodeDumpAction.DUMP_PRIMARY, None

        resolved_target_path = target_path.resolve()
        resolved_logged_path = existing_dump_record.path.resolve()

        # --- Case 1: Target path is the SAME as the primary logged path ---
        if resolved_target_path == resolved_logged_path:
            # Check if node mtime is newer than logged dump mtime
            node_mtime = node.mtime
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

        # --- Case 2: Target path is DIFFERENT from primary logged path ---
        is_calc_node = isinstance(node, orm.CalculationNode)
        is_sub_process = len(node.base.links.get_incoming(link_type=(LinkType.CALL_CALC, LinkType.CALL_WORK)).all()) > 0

        # Option A: Symlink Calculation
        if self.config.symlink_calcs and is_calc_node:
            return NodeDumpAction.SYMLINK, existing_dump_record

        # Option B: Force Duplicate Calculation Dump (if not symlinking)
        elif is_calc_node and is_sub_process and not self.config.only_top_level_calcs:
            return NodeDumpAction.DUMP_DUPLICATE, existing_dump_record

        # Option C: Standard Duplicate Dump (e.g., Workflows, non-symlinked Calcs)
        else:
            return NodeDumpAction.DUMP_DUPLICATE, existing_dump_record

    def _execute_skip(self):
        """Action: Skip dumping this node."""
        pass

    def _execute_symlink(self, node: orm.ProcessNode, target_path: Path, existing_dump_record: DumpRecord):
        """Action: Create a relative symlink to the primary dump location."""

        # Avoid creating symlink if target already exists (idempotency)
        if target_path.exists() or target_path.is_symlink():
            logger.warning(f'Target path {target_path.name} already exists. Skipping symlink creation.')
            # Ensure log entry reflects this link target even if skipped
            if target_path.resolve() not in {p.resolve() for p in existing_dump_record.symlinks if p.exists()}:
                try:
                    existing_dump_record.add_symlink(target_path.resolve())
                except OSError as e:
                    logger.error(f'Could not resolve path {target_path} to add to symlinks log: {e}')
            return  # Skip actual symlink creation

        try:
            source_path = existing_dump_record.path  # Absolute path to the original dump dir
            if not source_path.exists():
                logger.error(f'Source path {source_path} for node {node.pk} does not exist. Cannot symlink.')
                # No cleanup needed here, just log the error
                return

            link_location_dir = target_path.parent
            link_location_dir.mkdir(parents=True, exist_ok=True)
            relative_src_path = os.path.relpath(source_path, start=link_location_dir)

            os.symlink(relative_src_path, target_path, target_is_directory=True)

            # Add this new symlink location to the log entry
            existing_dump_record.add_symlink(target_path.resolve())

        except OSError as e:
            logger.error(f'Failed symlink creation for node {node.pk} at {target_path.name}: {e}')

    def _execute_update(self, node: orm.ProcessNode, target_path: Path, existing_dump_record: DumpRecord):
        """Action: Clean existing directory and perform a full dump."""

        node_pk = node.pk
        if not node_pk:
            return

        # Clean existing directory
        self.dump_paths.safe_delete_directory(path=target_path)

        # Prepare directory again
        self.dump_paths.prepare_directory(path_to_prepare=target_path)

        # Dump content
        self._dump_node_content(node, target_path)

        # Update stats on the existing log entry using the primary path
        existing_dump_record.update_stats()
        # ._calculate_and_update_stats(existing_dump_record.path, existing_dump_record)

    def _execute_dump_primary(self, node: orm.ProcessNode, target_path: Path):
        """Action: Perform a full dump as the primary location."""
        dump_record = None

        node_pk = node.pk
        if not node_pk:
            return

        try:
            # Prepare directory
            self.dump_paths.prepare_directory(path_to_prepare=target_path)

            # Create new log entry
            dump_record = DumpRecord(path=target_path.resolve())
            registry_key = ORM_TYPE_TO_REGISTRY[type(node)]
            self.dump_tracker.registries[cast(RegistryNameType, registry_key)].add_entry(node.uuid, dump_record)

            # Dump content
            self._dump_node_content(node, target_path)

            # Calculate and update stats for the new log entry
            self._calculate_and_update_stats(target_path, dump_record)

        except Exception as e:
            logger.error(f'Failed during DUMP_PRIMARY execution for node {node.pk}: {e}', exc_info=True)
            # Cleanup directory and log entry if primary dump failed
            self._cleanup_failed_dump(node, target_path, True)

    def _execute_dump_duplicate(self, node: orm.ProcessNode, target_path: Path, existing_dump_record: DumpRecord):
        """Action: Perform a full dump at a secondary location."""

        node_pk = node.pk
        if not node_pk:
            return

        try:
            # Prepare directory
            self.dump_paths.prepare_directory(path_to_prepare=target_path)

            # Add path to duplicates list in existing log entry
            existing_dump_record.add_duplicate(target_path.resolve())

            # Dump content
            self._dump_node_content(node, target_path)

        except Exception:
            # If duplicate dump fails, potentially clean the partial duplicate directory?
            self._cleanup_failed_dump(node, target_path, False)  # is_primary_dump=False

    def _validate_node_for_dump(self, node: orm.ProcessNode) -> bool:
        """Checks if the node is valid for dumping."""
        if not node.is_sealed and not self.config.dump_unsealed:
            msg = f'Process `{node.pk}` must be sealed before it can be dumped, or `--dump-unsealed` set to True.'
            raise ExportValidationError(msg)
        return True

    def _dump_node_content(
        self,
        node: orm.ProcessNode,
        target_path: Path,
    ):
        """Dumps the actual content (metadata, repo, children) (Original Logic)."""

        # 1. Write Metadata (Original Logic)
        self.metadata_writer._write(node, target_path)

        # 2. Ensure top-level safeguard exists (Original Logic)
        (target_path / DumpPaths.SAFEGUARD_FILE_NAME).touch(exist_ok=True)

        # 3. Dump Repo/IO or Recurse Children (Original Logic)
        if isinstance(node, orm.CalculationNode):
            self.repo_io_dumper._dump_calculation_content(node, target_path)
        elif isinstance(node, orm.WorkflowNode):
            # WorkflowWalker calls _dump_process_recursive_entry
            # Pass group context as potentially needed by recursive calls for symlink check
            self.workflow_walker._dump_children(node, target_path)  # Must ensure walker passes group context

    def _cleanup_failed_dump(
        self,
        node: orm.ProcessNode,
        target_path: Path,
        is_primary_dump: bool,
    ):
        """Cleans up directory and potentially log entry on failure (Original Logic)."""
        logger.warning(f'Attempting cleanup for failed dump of node {node.pk} at {target_path.name}')
        # Calling the utility as in original code
        self.dump_paths.safe_delete_directory(path=target_path)

        if is_primary_dump:
            registry_key = ORM_TYPE_TO_REGISTRY[type(node)]
            node_registry = self.dump_tracker.registries[registry_key]
            if not node_registry.del_entry(node.uuid):
                logger.warning(f'Could not find log entry to remove for failed primary dump of node {node.pk}')

    @staticmethod
    def _generate_child_node_label(index: int, link_triple: LinkTriple, append_pk: bool = True) -> str:
        """Generate clean directory label for child nodes during recursion (Original Logic)."""
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

        if append_pk:
            label_list += [str(node.pk)]

        node_label = '-'.join(label_list)
        # `CALL-` as part of the link labels also for MultiplyAddWorkChain -> Seems general enough, so remove
        node_label = node_label.replace('CALL-', '')
        # Original code had this replacement
        return node_label.replace('None-', '')


class NodeMetadataWriter:
    """Handles writing the aiida_node_metadata.yaml file."""

    def __init__(self, config: DumpConfig):
        self.config = config

    def _write(
        self,
        process_node: orm.ProcessNode,
        output_path: Path,
        output_filename: str = 'aiida_node_metadata.yaml',
    ) -> None:
        """Dump the selected ProcessNode properties, attributes, and extras to a YAML file."""
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
        with output_file.open('w', encoding='utf-8') as handle:
            # Use default_flow_style=None for better readability of nested structures
            yaml.dump(
                node_dict,
                handle,
                sort_keys=False,
                default_flow_style=None,
                indent=2,
            )


class NodeRepoIoDumper:
    """Handles dumping repository contents and linked I/O Data nodes."""

    def __init__(self, config: DumpConfig):
        self.config = config

    def _dump_calculation_content(self, calculation_node: orm.CalculationNode, output_path: Path) -> None:
        """Dump repository and I/O file contents for a CalculationNode."""
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
            # TODO: Possibly also use here explicit attribute chack rather than relying on try-except
            # TODO: Which might execute certain statements, then fail, and leave the result of prev. statements leftover
            try:
                output_links = calculation_node.base.links.get_outgoing(link_type=LinkType.CREATE).all()
                output_links_filtered = [link for link in output_links if link.link_label != 'retrieved']
                # TODO: Check here if other orm types, e.g. ArrayData would also be dumped
                # TODO: Also check for RemoteData if config option also remote is set
                # TODO: I have a PR open on that, but for the old version of the code
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
            except Exception as e:
                logger.error(f'Failed dumping outputs for calc {calculation_node.pk}: {e}')

    def _dump_calculation_io_files(
        self,
        parent_path: Path,
        link_triples: list[LinkTriple],
    ):
        """Helper to dump linked input/output Data nodes."""
        for link_triple in link_triples:
            node = link_triple.node
            link_label = link_triple.link_label
            if not self.config.flat:
                relative_parts = link_label.split('__')
                linked_node_path = parent_path.joinpath(*relative_parts)
            else:
                # Dump content directly into parent_path, letting copy_tree handle structure
                linked_node_path = parent_path

            if node.base.repository.list_object_names():
                linked_node_path.parent.mkdir(parents=True, exist_ok=True)
                node.base.repository.copy_tree(linked_node_path)

    @staticmethod
    def _generate_calculation_io_mapping(flat: bool = False) -> SimpleNamespace:
        """Helper to map internal names to directory names for CalcNode I/O."""
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

        :param dump_processor: A callable (like NodeManager.dump_process) that
                               takes a node and a target path to dump it.
        """
        self.dump_processor = dump_processor

    def _dump_children(self, workflow_node: orm.WorkflowNode, output_path: Path) -> None:
        """Find and recursively dump children of a WorkflowNode."""
        called_links = workflow_node.base.links.get_outgoing(link_type=(LinkType.CALL_CALC, LinkType.CALL_WORK)).all()
        called_links = sorted(called_links, key=lambda link_triple: link_triple.node.ctime)

        for index, link_triple in enumerate(called_links, start=1):
            child_node = link_triple.node
            # Use static method from NodeManager to generate label consistently
            from aiida.tools.dumping.executors.process import ProcessDumpExecutor

            child_label = ProcessDumpExecutor._generate_child_node_label(index=index, link_triple=link_triple)
            child_output_path = output_path / child_label
            assert isinstance(child_node, orm.ProcessNode)
            # Call the provided dump_processor function for the child
            self.dump_processor(
                child_node,
                child_output_path,
            )


class ReadmeGenerator:
    """Handles generating README.md files for process nodes."""

    def _generate(self, process_node: orm.ProcessNode, output_path: Path) -> None:
        """Generate README.md file in the specified output path."""
        import textwrap

        from aiida.cmdline.utils.ascii_vis import format_call_graph
        from aiida.cmdline.utils.common import (
            get_calcjob_report,
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
            f'\n## Node Info (`verdi node show {process_node.uuid}`)\n\n```\n{{get_node_info(process_node)}}\n```\n'
        )

        (output_path / 'README.md').write_text(_readme_string, encoding='utf-8')
