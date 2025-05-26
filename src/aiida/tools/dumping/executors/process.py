##########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Manager that deals with dumping a single ProcessNode."""

from __future__ import annotations

import contextlib
import os
from enum import Enum, auto
from pathlib import Path
from types import SimpleNamespace
from typing import TYPE_CHECKING, Callable, Optional, Tuple

import yaml

from aiida import orm
from aiida.common import LinkType, timezone
from aiida.common.log import AIIDA_LOGGER
from aiida.orm.utils import LinkTriple
from aiida.tools.archive.exceptions import ExportValidationError
from aiida.tools.dumping.config import DumpConfig
from aiida.tools.dumping.tracking import DumpRecord
from aiida.tools.dumping.utils.helpers import DumpStoreKeys
from aiida.tools.dumping.utils.paths import DumpPaths

if TYPE_CHECKING:
    from aiida.tools.dumping.tracking import DumpTracker
    from aiida.tools.dumping.utils.helpers import DumpTimes

__all__ = ('NodeMetadataWriter', 'NodeRepoIoDumper', 'ProcessDumpExecutor', 'ReadmeGenerator', 'WorkflowWalker')

logger = AIIDA_LOGGER.getChild('tools.dumping.managers.process')

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
    ERROR = auto()


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
        self.workflow_walker = WorkflowWalker(self._dump_process_recursive_entry)
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

        action, existing_log_entry = self._check_log_and_determine_action(
            node=process_node,
            target_path=target_path,
        )

        # Delegate execution based on the determined action
        try:
            if action == NodeDumpAction.SKIP:
                self._execute_skip(process_node)
            elif action == NodeDumpAction.SYMLINK:
                self._execute_symlink(process_node, target_path, existing_log_entry)
            elif action == NodeDumpAction.UPDATE:
                self._execute_update(process_node, target_path, existing_log_entry)
            elif action == NodeDumpAction.DUMP_PRIMARY:
                self._execute_dump_primary(process_node, target_path)
            elif action == NodeDumpAction.DUMP_DUPLICATE:
                self._execute_dump_duplicate(process_node, target_path, existing_log_entry)
            elif action == NodeDumpAction.ERROR:
                self._execute_error(process_node)
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

    def _dump_process_recursive_entry(
        self,
        process_node: orm.ProcessNode,
        target_path: Path,
    ):
        """Entry point for recursive calls from WorkflowWalker."""
        logger.debug(f'Recursive dump call for child node {process_node.pk} -> {target_path.name}')
        # Use the main dump logic for recursive calls as well
        self.dump(process_node=process_node, target_path=target_path)

    def _check_log_and_determine_action(
        self,
        node: orm.ProcessNode,
        target_path: Path,
    ) -> Tuple[NodeDumpAction, Optional[DumpRecord]]:
        """
        Checks the logger and node status to determine the appropriate dump action.
        This method should NOT have side effects like creating files/dirs or modifying logs.
        """
        store_key = DumpStoreKeys.from_instance(node)
        node_store = self.dump_tracker.get_store_by_name(store_key)
        existing_log_entry = node_store.get_entry(node.uuid)

        if not existing_log_entry:
            logger.debug(f'Node {node.pk} not found in log. Action: DUMP_PRIMARY')
            return NodeDumpAction.DUMP_PRIMARY, None

        # Node is logged. Check paths.
        try:
            resolved_target_path = target_path.resolve()
            resolved_logged_path = existing_log_entry.path.resolve()
        except (OSError, ValueError) as e:
            msg = (
                f'Error resolving/comparing paths for node {node.pk} ({target_path} vs {existing_log_entry.path}): {e}.'
                'Action: ERROR.'
            )
            logger.error(msg)
            return NodeDumpAction.ERROR, existing_log_entry

        # --- Case 1: Target path is the SAME as the primary logged path ---
        if resolved_target_path == resolved_logged_path:
            # Check if node mtime is newer than logged dump mtime
            node_mtime = node.mtime
            logged_dir_mtime = existing_log_entry.dir_mtime

            needs_update = False
            if logged_dir_mtime is None:
                needs_update = True
                logger.debug(f'Node {node.pk} needs update: Logged dir_mtime is missing.')
            # Ensure comparison is between timezone-aware datetimes
            elif node_mtime.astimezone(timezone.utc) > logged_dir_mtime.astimezone(timezone.utc):
                needs_update = True
                logger.debug(
                    f'Node {node.pk} needs update: Node mtime {node_mtime} > Logged dir_mtime {logged_dir_mtime}.'
                )

            if needs_update:
                logger.debug(f'Node {node.pk} exists at target, needs update. Action: UPDATE.')
                return NodeDumpAction.UPDATE, existing_log_entry
            else:
                logger.debug(f'Node {node.pk} exists at target, up-to-date. Action: SKIP.')
                return NodeDumpAction.SKIP, existing_log_entry

        # --- Case 2: Target path is DIFFERENT from primary logged path ---
        is_calc_node = isinstance(node, orm.CalculationNode)
        try:
            is_sub_process = (
                len(node.base.links.get_incoming(link_type=(LinkType.CALL_CALC, LinkType.CALL_WORK)).all()) > 0
            )
        except Exception:
            is_sub_process = False  # Default if link check fails

        # Option A: Symlink Calculation
        if self.config.symlink_calcs and is_calc_node:
            logger.debug(f'Node {node.pk} is calc, symlinking enabled. Action: SYMLINK.')
            return NodeDumpAction.SYMLINK, existing_log_entry

        # Option B: Force Duplicate Calculation Dump (if not symlinking)
        elif is_calc_node and is_sub_process and not self.config.only_top_level_calcs:
            logger.debug(f'Node {node.pk} is sub-calc, forcing duplicate dump. Action: DUMP_DUPLICATE.')
            return NodeDumpAction.DUMP_DUPLICATE, existing_log_entry

        # Option C: Standard Duplicate Dump (e.g., Workflows, non-symlinked Calcs)
        else:
            logger.debug(f'Node {node.pk} logged elsewhere, standard duplicate case. Action: DUMP_DUPLICATE.')
            return NodeDumpAction.DUMP_DUPLICATE, existing_log_entry

    def _execute_skip(self, node: orm.ProcessNode):
        """Action: Skip dumping this node."""
        logger.debug(f'Skipping node {node.pk} (already dumped and up-to-date or symlinked).')
        # No file operations needed

    def _execute_symlink(self, node: orm.ProcessNode, target_path: Path, existing_log_entry: DumpRecord):
        """Action: Create a relative symlink to the primary dump location."""
        logger.debug(f'Executing SYMLINK for node {node.pk} at {target_path.name}')

        # Avoid creating symlink if target already exists (idempotency)
        if target_path.exists() or target_path.is_symlink():
            logger.warning(f'Target path {target_path.name} already exists. Skipping symlink creation.')
            # Ensure log entry reflects this link target even if skipped
            if target_path.resolve() not in {p.resolve() for p in existing_log_entry.symlinks if p.exists()}:
                try:
                    existing_log_entry.add_symlink(target_path.resolve())
                except OSError as e:
                    logger.error(f'Could not resolve path {target_path} to add to symlinks log: {e}')
            return  # Skip actual symlink creation

        try:
            source_path = existing_log_entry.path  # Absolute path to the original dump dir
            if not source_path.exists():
                logger.error(f'Source path {source_path} for node {node.pk} does not exist. Cannot symlink.')
                # No cleanup needed here, just log the error
                return

            link_location_dir = target_path.parent
            link_location_dir.mkdir(parents=True, exist_ok=True)
            relative_src_path = os.path.relpath(source_path, start=link_location_dir)

            os.symlink(relative_src_path, target_path, target_is_directory=True)
            logger.info(f'Created relative symlink {target_path.name} -> {relative_src_path}')

            # Add this new symlink location to the log entry
            existing_log_entry.add_symlink(target_path.resolve())

        except OSError as e:
            logger.error(f'Failed symlink creation for node {node.pk} at {target_path.name}: {e}')
        except Exception as e:
            logger.error(f'Unexpected error during symlink creation for node {node.pk}: {e}', exc_info=True)

    def _execute_update(self, node: orm.ProcessNode, target_path: Path, existing_log_entry: DumpRecord):
        """Action: Clean existing directory and perform a full dump."""
        logger.info(f'Executing UPDATE for node {node.pk} at {target_path.name} due to mtime change.')
        try:
            # 1. Clean existing directory
            self.dump_paths.safe_delete_directory(directory_path=target_path)
            logger.debug(f'Cleaned existing directory for update: {target_path.name}')

            # 2. Prepare directory again
            self.dump_paths.prepare_directory(path_to_prepare=target_path)

            # 3. Dump content
            self._dump_node_content(node, target_path)

            # 4. Update stats on the existing log entry using the primary path
            self._calculate_and_update_stats(node.pk, existing_log_entry.path, existing_log_entry)

        except Exception as e:
            logger.error(f'Failed during UPDATE execution for node {node.pk}: {e}', exc_info=True)
            # If update fails, we might be left in a partial state. Avoid cleanup of primary log entry.

    def _execute_dump_primary(self, node: orm.ProcessNode, target_path: Path):
        """Action: Perform a full dump as the primary location."""
        logger.debug(f'Executing DUMP_PRIMARY for node {node.pk} at {target_path.name}')
        log_entry = None
        try:
            # 1. Prepare directory
            self.dump_paths.prepare_directory(path_to_prepare=target_path)

            # 2. Create new log entry
            log_entry = DumpRecord(path=target_path.resolve())
            store_key = DumpStoreKeys.from_instance(node)
            self.dump_tracker.get_store_by_name(store_key).add_entry(node.uuid, log_entry)
            logger.debug(f'Created primary log entry for node {node.pk}')

            # 3. Dump content
            self._dump_node_content(node, target_path)

            # 4. Calculate and update stats for the new log entry
            self._calculate_and_update_stats(node.pk, target_path, log_entry)

        except Exception as e:
            logger.error(f'Failed during DUMP_PRIMARY execution for node {node.pk}: {e}', exc_info=True)
            # Cleanup directory and log entry if primary dump failed
            self._cleanup_failed_dump(node, target_path, True)

    def _execute_dump_duplicate(self, node: orm.ProcessNode, target_path: Path, existing_log_entry: DumpRecord):
        """Action: Perform a full dump at a secondary location."""
        logger.debug(f'Executing DUMP_DUPLICATE for node {node.pk} at {target_path.name}')
        try:
            # 1. Prepare directory
            self.dump_paths.prepare_directory(path_to_prepare=target_path)

            # 2. Add path to duplicates list in existing log entry
            existing_log_entry.add_duplicate(target_path.resolve())
            logger.debug(f'Added duplicate path {target_path.name} to log for node {node.pk}')

            # 3. Dump content
            self._dump_node_content(node, target_path)

            # 4. Update stats on the *primary* log entry (optional, could skip for duplicates)
            #    Recalculating stats based on primary path might be redundant here unless content changed
            #    Let's keep it consistent for now.
            self._calculate_and_update_stats(node.pk, existing_log_entry.path, existing_log_entry)

        except Exception as e:
            logger.error(f'Failed during DUMP_DUPLICATE execution for node {node.pk}: {e}', exc_info=True)
            # If duplicate dump fails, potentially clean the partial duplicate directory?
            self._cleanup_failed_dump(node, target_path, False)  # is_primary_dump=False

    def _execute_error(self, node: orm.ProcessNode):
        """Action: Log error, do nothing else."""
        logger.error(f'Executing ERROR action for node {node.pk}. Aborting dump for this node.')
        # No file operations

    # --- Helper methods ---
    def _validate_node_for_dump(self, node: orm.ProcessNode) -> bool:
        """Checks if the node is valid for dumping (Original Logic)."""
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
        logger.debug(f'Dumping content for node {node.pk} into {target_path.name}')

        # 1. Write Metadata (Original Logic)
        self.metadata_writer._write(node, target_path)
        logger.debug(f'Metadata written for node {node.pk}')

        # 2. Ensure top-level safeguard exists (Original Logic)
        (target_path / DumpPaths.SAFEGUARD_FILE_NAME).touch(exist_ok=True)

        # 3. Dump Repo/IO or Recurse Children (Original Logic)
        if isinstance(node, orm.CalculationNode):
            self.repo_io_dumper._dump_calculation_content(node, target_path)
            logger.debug(f'Calculation content dumped for node {node.pk}')
        elif isinstance(node, orm.WorkflowNode):
            # WorkflowWalker calls _dump_process_recursive_entry
            # Pass group context as potentially needed by recursive calls for symlink check
            self.workflow_walker._dump_children(node, target_path)  # Must ensure walker passes group context
            logger.debug(f'Workflow children dumped for node {node.pk}')

    def _calculate_and_update_stats(self, node_pk: int, path_to_stat: Path, log_entry: DumpRecord):
        """Calculates directory stats and updates the log entry (Original Logic)."""
        logger.debug(f'Calculating stats for node {node_pk} directory: {path_to_stat.name}')
        try:
            # Calling the utility as in original code
            dir_mtime, dir_size = self.dump_paths.get_directory_stats(path_to_stat)
            log_entry.dir_mtime = dir_mtime
            log_entry.dir_size = dir_size
            logger.debug(f'Updated stats for node {node_pk}: mtime={dir_mtime}, size={dir_size} bytes')
        except Exception as e:
            # Original code didn't explicitly catch errors here, but added logging is good
            logger.warning(f'Could not calculate/update stats for node {node_pk} at {path_to_stat}: {e}')

    def _cleanup_failed_dump(
        self,
        node: orm.ProcessNode,
        target_path: Path,
        is_primary_dump: bool,
    ):
        """Cleans up directory and potentially log entry on failure (Original Logic)."""
        logger.warning(f'Attempting cleanup for failed dump of node {node.pk} at {target_path.name}')
        try:
            # Calling the utility as in original code
            self.dump_paths.safe_delete_directory(directory_path=target_path)
            logger.info(f'Cleaned up directory {target_path.name} for failed node {node.pk}')

            if is_primary_dump:
                store_key = DumpStoreKeys.from_instance(node)
                node_store = self.dump_tracker.get_store_by_name(store_key)
                if node_store.del_entry(node.uuid):
                    logger.info(f'Removed log entry for failed primary dump of node {node.pk}')
                else:
                    logger.warning(f'Could not find log entry to remove for failed primary dump of node {node.pk}')

        except Exception as cleanup_e:
            msg = (f'Failed during cleanup for node {node.pk} at {target_path.name}: {cleanup_e}',)
            logger.error(msg, exc_info=True)

    @staticmethod
    def _generate_node_directory_name(node: orm.ProcessNode, append_pk: bool = True) -> Path:
        """Generates the directory name for a specific node."""
        # Calling the utility function as in the original code
        return DumpPaths.get_default_dump_path(node)

    @staticmethod
    def _generate_child_node_label(index: int, link_triple: LinkTriple, append_pk: bool = True) -> str:
        """Generate clean directory label for child nodes during recursion (Original Logic)."""
        # IMPORTANT: Keeping the exact logic from the originally provided file
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
        try:
            with output_file.open('w', encoding='utf-8') as handle:
                # Use default_flow_style=None for better readability of nested structures
                yaml.dump(
                    node_dict,
                    handle,
                    sort_keys=False,
                    default_flow_style=None,
                    indent=2,
                )
        except Exception as e:
            logger.error(f'Failed to write YAML metadata for node {process_node.pk}: {e}')


class NodeRepoIoDumper:
    """Handles dumping repository contents and linked I/O Data nodes."""

    def __init__(self, config: DumpConfig):
        self.config = config

    def _dump_calculation_content(self, calculation_node: orm.CalculationNode, output_path: Path) -> None:
        """Dump repository and I/O file contents for a CalculationNode."""
        io_dump_mapping = self._generate_calculation_io_mapping(flat=self.config.flat)

        # Dump the main repository contents
        try:
            repo_target = output_path / io_dump_mapping.repository
            repo_target.mkdir(parents=True, exist_ok=True)

            calculation_node.base.repository.copy_tree(repo_target)
        except Exception as e:
            logger.error(f'Failed copying repository for calc {calculation_node.pk}: {e}')

        # Dump the repository contents of `outputs.retrieved` if it exists
        if hasattr(calculation_node.outputs, 'retrieved'):
            try:
                retrieved_target = output_path / io_dump_mapping.retrieved
                retrieved_target.mkdir(parents=True, exist_ok=True)
                calculation_node.outputs.retrieved.base.repository.copy_tree(retrieved_target)
            except Exception as e:
                logger.error(f'Failed copying retrieved output for calc {calculation_node.pk}: {e}')
        else:
            logger.debug(f"No 'retrieved' output node found for calc {calculation_node.pk}.")

        # Dump the node_inputs (linked Data nodes)
        if self.config.include_inputs:
            try:
                input_links = calculation_node.base.links.get_incoming(link_type=LinkType.INPUT_CALC).all()
                if input_links:
                    input_path = output_path / io_dump_mapping.inputs
                    # NOTE: Not needed, done in _dump_calculation_io_files
                    # input_path.mkdir(parents=True, exist_ok=True)
                    self._dump_calculation_io_files(
                        parent_path=input_path,
                        link_triples=input_links,
                    )
            except Exception as e:
                logger.error(f'Failed dumping inputs for calc {calculation_node.pk}: {e}')

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
            try:
                if not self.config.flat:
                    relative_parts = link_label.split('__')
                    linked_node_path = parent_path.joinpath(*relative_parts)
                else:
                    # Dump content directly into parent_path, letting copy_tree handle structure
                    linked_node_path = parent_path

                if node.base.repository.list_object_names():
                    linked_node_path.parent.mkdir(parents=True, exist_ok=True)
                    node.base.repository.copy_tree(linked_node_path)
            except Exception as e:
                logger.warning(f'Failed copying IO node {node.pk} (link: {link_label}): {e}')

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
        try:
            called_links = workflow_node.base.links.get_outgoing(
                link_type=(LinkType.CALL_CALC, LinkType.CALL_WORK)
            ).all()
            called_links = sorted(called_links, key=lambda link_triple: link_triple.node.ctime)
        except Exception as e:
            logger.error(f'Failed getting children for workflow {workflow_node.pk}: {e}')
            return

        for index, link_triple in enumerate(called_links, start=1):
            child_node = link_triple.node
            # Use static method from NodeManager to generate label consistently
            from aiida.tools.dumping.executors.process import ProcessDumpExecutor

            child_label = ProcessDumpExecutor._generate_child_node_label(index=index, link_triple=link_triple)
            child_output_path = output_path / child_label
            assert isinstance(child_node, orm.ProcessNode)
            try:
                # Call the provided dump_processor function for the child
                self.dump_processor(
                    child_node,
                    child_output_path,
                )
            except Exception as e:
                logger.error(
                    f'Failed dumping child node {child_node.pk} of workflow {workflow_node.pk}: {e}',
                    exc_info=True,
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
        try:
            _readme_string += (
                f'\n## Process Status (`verdi process status {pk}`)\n\n```\n{format_call_graph(process_node)}\n```\n'
            )
        except Exception as e:
            logger.debug(f'Could not format call graph for README: {e}')

        try:
            if isinstance(process_node, orm.CalcJobNode):
                report = get_calcjob_report(process_node)
            elif isinstance(process_node, orm.WorkChainNode):
                report = get_workchain_report(node=process_node, levelname='REPORT', indent_size=2, max_depth=None)
            elif isinstance(process_node, (orm.CalcFunctionNode, orm.WorkFunctionNode)):
                report = get_process_function_report(process_node)
            else:
                report = 'N/A'
            _readme_string += f'\n## Process Report (`verdi process report {pk}`)\n\n```\n{report}\n```\n'
        except Exception as e:
            logger.debug(f'Could not generate process report for README: {e}')

        try:
            _readme_string += (
                f'\n## Node Info (`verdi node show {process_node.uuid}`)\n\n```\n{{get_node_info(process_node)}}\n```\n'
            )
        except Exception as e:
            logger.debug(f'Could not get node info for README: {e}')

        try:
            (output_path / 'README.md').write_text(_readme_string, encoding='utf-8')
        except Exception as e:
            logger.error(f'Failed to write README for node {process_node.pk}: {e}')
