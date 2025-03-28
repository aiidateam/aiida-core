###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Functionality for mirroring of a Collection of AiiDA ORM entities."""

from __future__ import annotations

import os
from datetime import datetime
from pathlib import Path
from typing import Any

from aiida import orm
from aiida.common.log import AIIDA_LOGGER
from aiida.common.progress_reporter import (
    get_progress_reporter,
    set_progress_bar_tqdm,
)
from aiida.tools.mirror.collection import BaseCollectionMirror
from aiida.tools.mirror.config import (
    GroupMirrorConfig,
    MirrorMode,
    NodeCollectorConfig,
    ProcessMirrorConfig,
)
from aiida.tools.mirror.logger import MirrorLog, MirrorLogger
from aiida.tools.mirror.process import ProcessMirror
from aiida.tools.mirror.utils import (
    MirrorPaths,
    NodeMirrorKeyMapper,
    generate_group_default_mirror_path,
    generate_process_default_mirror_path,
    load_given_group,
)

logger = AIIDA_LOGGER.getChild('tools.mirror.group')

# NOTE: `load_mirror_logger` could be put in general Parent cparent class
# NOTE: Accessing via `group.nodes` might be nice, keep in mind
# NOTE: Should the `mirror_logger` even be passed as an argument???
# TODO: Don't update the logger with the UUID of a symlinked calculation as keys must be unique
# TODO: Possibly add another `symlink` attribute to `MirrorLog` which can hold a list of symlinks
# TODO: Ignore for now, as I would need to retrieve the list of links, append to it, and assign again
# TODO: Only allow for "pure" sequences of Calculation- or WorkflowNodes, or also mixed?
# TODO: If the latter possibly also have directory creation in the loop


class GroupMirror(BaseCollectionMirror):
    """Class to handle mirroring of a group of AiiDA ORM entities."""

    def __init__(
        self,
        group: orm.Group,
        mirror_mode: MirrorMode | None = None,
        mirror_paths: MirrorPaths | None = None,
        # NOTE: This should be part of the logger...
        last_mirror_time: datetime | None = None,
        mirror_logger: MirrorLogger | None = None,
        node_collector_config: NodeCollectorConfig | None = None,
        group_mirror_config: GroupMirrorConfig | None = None,
        process_mirror_config: ProcessMirrorConfig | None = None,
    ):
        """Initialize the GroupMirror class."""

        if mirror_paths is None:
            default_mirror_path = generate_group_default_mirror_path()
            mirror_paths = MirrorPaths(parent=Path.cwd(), child=default_mirror_path)

        super().__init__(
            mirror_mode=mirror_mode,
            mirror_paths=mirror_paths,
            last_mirror_time=last_mirror_time,
            mirror_logger=mirror_logger,
            node_collector_config=node_collector_config,
        )

        self.group = load_given_group(group)

        self.group_mirror_config = group_mirror_config or GroupMirrorConfig()
        self.process_mirror_config = process_mirror_config or ProcessMirrorConfig()
        # FIXME: This is duplicated/overwritten here because, due to the recursive nature of the Process mirroring
        # FIXME: I need to pass the option to both, the GroupMirror and the ProcessMirror
        self.process_mirror_config.symlink_calcs = self.group_mirror_config.symlink_calcs

    # staticmethod so I can use it before instantiation of the GroupDumper, as that will need the subpath already
    @staticmethod
    def get_group_subpath(group) -> Path:
        group_entry_point = group.entry_point
        if group_entry_point is None:
            return Path(group.label)

        group_entry_point_name = group_entry_point.name
        if group_entry_point_name == 'core':
            return Path(f'{group.label}')
        if group_entry_point_name == 'core.import':
            return Path('import') / f'{group.label}'

        group_subpath = Path(*group_entry_point_name.split('.'))

        return group_subpath / f'{group.label}'

    def _mirror_processes(self, processes: list[orm.CalculationNode] | list[orm.WorkflowNode]) -> None:
        """Dump a list of AiiDA calculations or workflows to disk.

        :param processes: List of AiiDA calculations or workflows from the ``ProcessesToMirrorContainer``.
        """
        # NOTE: In principle, a node can only be once in a group

        if len(list(processes)) == 0:
            return

        # Setup common resources needed for mirroring
        process_type_path = self.mirror_paths.absolute / NodeMirrorKeyMapper.get_key_from_instance(
            node_inst=processes[0]
        )
        process_type_path.mkdir(exist_ok=True, parents=True)

        # NOTE: This seems a bit hacky. Can probably be improved
        current_store_type = NodeMirrorKeyMapper.get_key_from_instance(node_inst=next(iter(processes)))
        other_store_type = 'calculations' if current_store_type == 'workflows' else 'workflows'

        current_store = getattr(self.mirror_logger.log, current_store_type)
        other_store = getattr(self.mirror_logger.log, other_store_type)
        self.current_store = current_store
        self.other_store = other_store

        set_progress_bar_tqdm()

        # Mirror each process with progress tracking
        with get_progress_reporter()(desc='Mirroring new processes', total=len(processes)) as progress:
            for process in processes:
                self._mirror_process(
                    process=process,
                    process_type_path=process_type_path,
                )
                progress.update()

    def _create_symlink_from_store(self, process_uuid: str, store_instance: Any, process_mirror_path: Path) -> bool:
        """Create a symlink from an existing entry in a store to a new path.

        :param process_uuid: The UUID of the process to link
        :param store_instance: The store instance (current_store or other_store)
        :param process_mirror_path: The target path for the symlink
        :return: True if the symlink was created or already exists, False if UUID not in store
        """
        if process_uuid not in store_instance.entries.keys():
            return False

        if not process_mirror_path.exists():
            process_mirror_path.parent.mkdir(exist_ok=True, parents=True)
            try:
                os.symlink(
                    src=store_instance.entries[process_uuid].path,
                    dst=process_mirror_path,
                )
                # TODO: If this works here, call `add_link` to the MirrorLog to extend an existing MirrorLog
            except FileExistsError:
                # For debugging
                raise
                pass

        return True

    def _mirror_process(
        self,
        process: orm.CalculationNode | orm.WorkflowNode,
        process_type_path: Path,
    ) -> None:
        """Mirror a single process to disk.

        :param process: An AiiDA calculation or workflow node to mirror
        :param process_type_path: Path where processes of this type are stored
        :param process_mirror: The ProcessMirror instance to use
        """
        process_mirror_path = process_type_path / generate_process_default_mirror_path(
            process_node=process, prefix=None
        )

        process_paths = MirrorPaths(
            parent=process_mirror_path.parent,
            child=process_mirror_path.name,
        )

        process_mirror_inst = ProcessMirror(
            process_node=process,
            mirror_mode=self.mirror_mode,
            mirror_paths=process_paths,
            last_mirror_time=self.last_mirror_time,
            process_mirror_config=self.process_mirror_config,
            mirror_logger=self.mirror_logger,
        )

        if not self.group_mirror_config.symlink_calcs:
            # Case: symlink_duplicates is disabled
            process_mirror_inst.do_mirror(top_level_caller=False)

        else:
            # Try to create symlink from current_store first
            symlinked = self._create_symlink_from_store(
                process_uuid=process.uuid,
                store_instance=self.current_store,
                process_mirror_path=process_mirror_path,
            )

            # If not found in current_store, try other_store
            if not symlinked:
                symlinked = self._create_symlink_from_store(
                    process_uuid=process.uuid,
                    store_instance=self.other_store,
                    process_mirror_path=process_mirror_path,
                )

            # If not found in either store, create a new mirror
            if not symlinked:
                process_mirror_inst.do_mirror(process_node=process, output_path=process_mirror_path)

        # This happens regardless of which case was executed
        self.current_store.add_entry(
            uuid=process.uuid,
            entry=MirrorLog(path=process_mirror_path, time=datetime.now().astimezone()),
        )

    def _mirror_process_collections(self) -> None:
        """Handle mirroring of different process collections."""

        # First, mirror calculations and then workflows, as sub-calculations of workflows can be symlinked
        for process_type in ('calculations', 'workflows'):
            processes = getattr(self.node_container, process_type)
            if len(processes) > 0:
                msg = f'Mirroring {len(processes)} {process_type}s...'
                logger.report(msg)
                self._mirror_processes(processes=processes)
            else:
                msg = f'No {process_type} to mirror in group `{self.group.label}`.'
                logger.report(msg)

    def do_mirror(self, top_level_caller: bool = False) -> None:
        """Top-level method that actually performs the mirroring of the AiiDA data for the collection.

        :return: None
        """

        self.pre_mirror(top_level_caller=top_level_caller)
        self.node_container = self.get_node_container(group=self.group)

        self._mirror_process_collections()

        self.post_mirror()

    # @cached_property
    # def processes_to_delete(self) -> NodeContainer:
    #     """Get the processes to mirror from the collection of nodes.

    #     Only re-evaluates the processes, if not already set.

    #     :return: Instance of a ``ProcessesToMirrorContainer``, that holds the selected calculations and workflows.
    #     """
    #     if not self.group_mirror_config.delete_missing:
    #         return NodeContainer(calculations=[], workflows=[])
    #     return self._get_processes_to_delete()

    # def _get_processes_to_delete(self) -> NodeContainer:
    #     mirror_logger = self.mirror_logger
    #     log = mirror_logger.log

    #     # Cannot use QB here because, when node deleted, it's not in the DB anymore
    #     mirrored_uuids = set(list(log.calculations.entries.keys()) + list(log.workflows.entries.keys()))

    #     # One could possibly filter here since last mirror time, however
    #     # it is highly likely that the last mirror command with deletion was run a while ago
    #     # So I cannot filter by last mirror time, but should probably take the whole set

    #     # This should not be needed anymore...
    #     # if self.group:
    #     #     qb = orm.QueryBuilder()
    #     #     qb.append(orm.Group, filters={'uuid': self.group.uuid}, tag='group')
    #     #     qb.append(orm.ProcessNode, with_group='group', project=['uuid'])
    #     #     group_nodes = cast(set[str], set(qb.all(flat=True)))
    #     # else:

    #     assert self.group_nodes is not None
    #     group_nodes = set(self.group_nodes)

    #     # Don't restrict here to only top-level processes, as all file paths, also for sub-processes are actually
    #     # created and stored in the log
    #     # profile_uuids = set([process.uuid for process in profile_processes if process.caller is None])
    #     to_delete_uuids = list(mirrored_uuids - group_nodes)

    #     # TODO: Return ProcessContainer here -> For this, need to load ORM entities (again...) and
    #     # categorize by workflow or calculation...
    #     # Re-use code from _get_processes_to_mirror, move into function
    #     # to_delete_orms =

    #     return to_delete_uuids

    # def delete_processes(self):
    #     # print(f'TO_MIRROR_PROCESSES: {to_mirror_processes}')
    #     # print(f'TO_DELETE_PROCESSES: {to_delete_processes}')

    #     for to_delete_uuid in self.processes_to_delete:
    #         delete_missing_node_dir(mirror_logger=self.mirror_logger, to_delete_uuid=to_delete_uuid)

    #     # TODO: Add also logging for node/path deletion?
