###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Functionality for dumping of a Collection of AiiDA ORM entities."""

from __future__ import annotations
import json
import os
from datetime import datetime
from functools import cached_property
from pathlib import Path

from aiida import orm
from aiida.common.log import AIIDA_LOGGER
from aiida.tools.dumping.collector import NodeContainer, NodeDumpCollector
from aiida.tools.dumping.config import (
    DumpMode,
    GroupDumpConfig,
    NodeCollectorConfig,
    ProcessDumpConfig,
)
from aiida.tools.dumping.logger import DumpLog, DumpLogger
from aiida.tools.dumping.process import ProcessDumper
from aiida.tools.dumping.utils import (
    NodeDumpKeyMapper,
    SafeguardFileMapping,
    delete_missing_node_dir,
    generate_process_default_dump_path,
    load_given_group,
    prepare_dump_path,
    DumpPaths,
    load_dump_logger,
)
from aiida.common.progress_reporter import (
    get_progress_reporter,
    set_progress_bar_tqdm,
    set_progress_reporter,
    create_callback,
)

logger = AIIDA_LOGGER.getChild('tools.dumping')

# NOTE: `load_dump_logger` could be put in general Parent cparent class
# NOTE: Accessing via `group.nodes` might be nice, keep in mind
# NOTE: Should the `dump_logger` even be passed as an argument???


class GroupDumper:
    """Class to handle dumping of a collection of AiiDA ORM entities."""

    def __init__(
        self,
        group: orm.Group,
        dump_mode: DumpMode,
        dump_paths: DumpPaths,
        # NOTE: This should be part of the logger...
        last_dump_time: datetime | None = None,
        dump_logger: DumpLogger | None = None,
        node_collector_config: NodeCollectorConfig | None = None,
        process_dump_config: ProcessDumpConfig | None = None,
        group_dump_config: GroupDumpConfig | None = None,
    ):
        """Initialize the CollectionDumper.

        :param dump_logger: Logger for the dumping (gets instantiated).
        :param group: AiiDA group of which the nodes should be dumped.
        :param process_dumper: Process dumper instance or None (gets instantiated).
        :param processes_to_dump: Optional precomputed processes to dump.
        """

        self.dump_mode = dump_mode
        self.dump_paths = dump_paths
        self.last_dump_time = last_dump_time
        self.dump_logger = dump_logger

        self.group = load_given_group(group)

        self.node_collector_config = node_collector_config or NodeCollectorConfig()
        self.process_dump_config = process_dump_config or ProcessDumpConfig()
        self.group_dump_config = group_dump_config or GroupDumpConfig()

        if not dump_logger:
            if self.dump_mode.OVERWRITE:
                self.dump_logger = dump_logger = DumpLogger(dump_paths=self.dump_paths)
            else:
                self.dump_logger = load_dump_logger()

        # self.include_processes = self.group_dump_config.include_processes
        # self.include_data = self.group_dump_config.include_data
        # self.symlink_duplicates = self.group_dump_config.symlink_duplicates
        self.delete_missing = self.group_dump_config.delete_missing

        # self.only_top_level_calcs = self.group_dump_config.only_top_level_calcs
        # self.only_top_level_workflows = self.group_dump_config.only_top_level_workflows
        # self.filter_nodes_by_last_dump_time = self.group_dump_config.filter_by_last_dump_time

        # Try to get `last_dump_time` from dumping safeguard file, if it already exsits

    def get_node_container(self) -> NodeContainer:
        """
        Returns a NodeContainer by collecting nodes using the NodeDumpCollector.

        Returns:
            NodeContainer: The collected node container
        """
        # import ipdb; ipdb.set_trace()
        node_collector = NodeDumpCollector(
            config=self.node_collector_config,
            last_dump_time=self.last_dump_time,
            dump_logger=self.dump_logger,
        )
        return node_collector.collect(
            group=self.group,
        )

    # @cached_property
    # def processes_to_dump(self) -> NodeContainer:
    #     """Get the processes to dump from the collection of nodes.

    #     Only re-evaluates the processes, if not already set.

    #     :return: Instance of a ``ProcessesToDumpContainer``, that holds the selected calculations and workflows.
    #     """

    #     return self._get_processes_to_dump()

    @cached_property
    def processes_to_delete(self) -> NodeContainer:
        """Get the processes to dump from the collection of nodes.

        Only re-evaluates the processes, if not already set.

        :return: Instance of a ``ProcessesToDumpContainer``, that holds the selected calculations and workflows.
        """
        if not self.delete_missing:
            return NodeContainer(calculations=[], workflows=[])
        return self._get_processes_to_delete()

    def _get_processes_to_delete(self) -> NodeContainer:
        dump_logger = self.dump_logger
        log = dump_logger.log

        # Cannot use QB here because, when node deleted, it's not in the DB anymore
        dumped_uuids = set(list(log.calculations.entries.keys()) + list(log.workflows.entries.keys()))

        # One could possibly filter here since last dump time, however
        # it is highly likely that the last dump command with deletion was run a while ago
        # So I cannot filter by last dump time, but should probably take the whole set

        # This should not be needed anymore...
        # if self.group:
        #     qb = orm.QueryBuilder()
        #     qb.append(orm.Group, filters={'uuid': self.group.uuid}, tag='group')
        #     qb.append(orm.ProcessNode, with_group='group', project=['uuid'])
        #     group_nodes = cast(set[str], set(qb.all(flat=True)))
        # else:

        assert self.group_nodes is not None
        group_nodes = set(self.group_nodes)

        # Don't restrict here to only top-level processes, as all file paths, also for sub-processes are actually
        # created and stored in the log
        # profile_uuids = set([process.uuid for process in profile_processes if process.caller is None])
        to_delete_uuids = list(dumped_uuids - group_nodes)

        # TODO: Return ProcessContainer here -> For this, need to load ORM entities (again...) and
        # categorize by workflow or calculation...
        # Re-use code from _get_processes_to_dump, move into function
        # to_delete_orms =

        return to_delete_uuids

    def delete_processes(self):
        # print(f'TO_DUMP_PROCESSES: {to_dump_processes}')
        # print(f'TO_DELETE_PROCESSES: {to_delete_processes}')

        for to_delete_uuid in self.processes_to_delete:
            delete_missing_node_dir(dump_logger=self.dump_logger, to_delete_uuid=to_delete_uuid)

        # TODO: Add also logging for node/path deletion?

    def _dump_processes(self, processes: list[orm.CalculationNode] | list[orm.WorkflowNode]) -> None:
        """Dump a list of AiiDA calculations or workflows to disk.

        :param processes: List of AiiDA calculations or workflows from the ``ProcessesToDumpContainer``.
        """

        if len(list(processes)) == 0:
            return

        # TODO: Only allow for "pure" sequences of Calculation- or WorkflowNodes, or also mixed?
        # TODO: If the latter possibly also have directory creation in the loop

        sub_path = self.dump_paths.absolute / NodeDumpKeyMapper.get_key_from_instance(node_inst=processes[0])
        sub_path.mkdir(exist_ok=True, parents=True)

        logger_attr = NodeDumpKeyMapper.get_key_from_instance(node_inst=next(iter(processes)))
        # ! `getattr` gives a reference to the actual object, thus I can update the store directly
        current_store = getattr(self.dump_logger.log, logger_attr)

        process_dumper = ProcessDumper(
            dump_parent_path=sub_path.parent,
            dump_sub_path=sub_path.name,
            last_dump_time=self.last_dump_time,
            dump_mode=self.dump_mode,
            process_dump_config=self.process_dump_config,
            dump_logger=self.dump_logger,
        )

        # import ipdb; ipdb.set_trace()

        set_progress_bar_tqdm()
        with get_progress_reporter()(desc=f'Mirroring new processes', total=len(processes)) as progress:
            for process in processes:
                process_dump_path = sub_path / generate_process_default_dump_path(process_node=process, prefix=None)

                if self.group_dump_config.symlink_duplicates and process.uuid in current_store.entries.keys():
                    if process_dump_path.exists():
                        continue
                    else:
                        process_dump_path.parent.mkdir(exist_ok=True, parents=True)
                        # breakpoint()
                        try:
                            os.symlink(
                                src=current_store.entries[process.uuid].path,
                                dst=process_dump_path,
                            )
                            # TODO: If this works here, call `add_link` to the DumpLog to extend an existing DumpLog
                        except FileExistsError:
                            pass

                else:
                    # TODO: Don't update the logger with the UUID of a symlinked calculation as keys must be unique
                    # TODO: Possibly add another `symlink` attribute to `DumpLog` which can hold a list of symlinks
                    # TODO: Ignore for now, as I would need to retrieve the list of links, append to it, and assign again

                    # process_dumper._dump_calculation(calculation_node=process, output_path=process_dump_path)
                    # ! TODO: Add DumpLogger here, such that sub-calculations of workflows are also registered in the
                    # ! dumping, otherwise they end up duplicated, as the registration is done here in the for loop

                    process_dumper.dump(process_node=process, output_path=process_dump_path)

                current_store.add_entry(
                    uuid=process.uuid,
                    entry=DumpLog(path=process_dump_path, time=datetime.now().astimezone()),
                )

                progress.update(1)

    def _pre_mirror(self) -> None:
        """_summary_"""
        _ = prepare_dump_path(
            path_to_validate=self.dump_paths.absolute,
            dump_mode=self.dump_mode,
            safeguard_file=SafeguardFileMapping.GROUP.value,
            top_level_caller=True,
        )

        safeguard_file_path = self.dump_paths.absolute / SafeguardFileMapping.GROUP.value

        try:
            with safeguard_file_path.open('r') as fhandle:
                last_dump_time = datetime.fromisoformat(fhandle.readlines()[-1].strip().split()[-1]).astimezone()
        except (IndexError, FileNotFoundError):
            last_dump_time = None

        self.safeguard_file_path = safeguard_file_path
        self.last_dump_time = last_dump_time
        self.current_dump_time = datetime.now().astimezone()

    def _post_mirror(self) -> None:
        """_summary_"""
        self.dump_logger.save_log()

        # Append the current dump time to dumping safeguard file
        with self.safeguard_file_path.open('a') as fhandle:
            fhandle.write(f'Last profile mirror time: {self.current_dump_time.isoformat()}\n')

    def mirror(self) -> None:
        """Top-level method that actually performs the dumping of the AiiDA data for the collection.

        :return: None
        """

        self._pre_mirror()

        # Update the `last_dump_time` now, rather than after the dumping, as writing files to disk can take some time, and
        # which processes should be dumped is evaluated beforehand (here)

        node_container = self.get_node_container()

        for process_type in ('calculations', 'workflows'):
            processes = getattr(node_container, process_type)
            if len(processes) > 0:
                logger.report(f'Dumping {process_type}')
                self._dump_processes(processes=processes)
            else:
                logger.report(f'No {process_type} to dump.')

        self._post_mirror()
