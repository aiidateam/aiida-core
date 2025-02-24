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

import ipdb
import os
from datetime import datetime
from pathlib import Path
from typing import cast
from functools import cached_property

from aiida import orm
from aiida.common.log import AIIDA_LOGGER
from aiida.tools.dumping.base import BaseDumper
from aiida.tools.dumping.config import BaseDumpConfig, ProcessDumpConfig, ProfileDumpConfig
from aiida.tools.dumping.logger import DumpLog, DumpLogger
from aiida.tools.dumping.process import ProcessDumper
from aiida.tools.dumping.utils import (
    NodeDumpKeyMapper,
    ProcessContainer,
    delete_missing_node_dir,
    generate_process_default_dump_path,
    load_given_group,
    do_filter_nodes
)

logger = AIIDA_LOGGER.getChild('tools.dumping')


class GroupDumper(BaseDumper):
    """Class to handle dumping of a collection of AiiDA ORM entities."""

    def __init__(
        self,
        dump_parent_path: Path | None = None,
        dump_sub_path: Path | None = None,
        last_dump_time: datetime | None = None,
        base_dump_config: BaseDumpConfig | None = None,
        process_dump_config: ProcessDumpConfig | None = None,
        # Need to pass the `profile_dump_config` to have access to some of the top-level settings
        profile_dump_config: ProfileDumpConfig | None = None,
        dump_logger: DumpLogger | None = None,
        group: orm.Group | str | None = None,
    ):
        """Initialize the CollectionDumper.

        :param base_dump_config: Base dumper instance or None (gets instantiated).
        :param dump_logger: Logger for the dumping (gets instantiated).
        :param group: AiiDA group of which the nodes should be dumped.
        :param process_dumper: Process dumper instance or None (gets instantiated).
        :param processes_to_dump: Optional precomputed processes to dump.
        """

        super().__init__(
            dump_parent_path=dump_parent_path,
            dump_sub_path=dump_sub_path,
            last_dump_time=last_dump_time,
            dump_logger=dump_logger,
            base_dump_config=base_dump_config,
        )

        self.group: orm.Group | None
        if group is not None:
            # This is only required to ensure we deal with `orm.Group` and not a `str`
            self.group = load_given_group(group)
        else:
            self.group = None

        self.base_dump_config = base_dump_config or BaseDumpConfig()
        self.process_dump_config = process_dump_config or ProcessDumpConfig()
        self.profile_dump_config = profile_dump_config or ProfileDumpConfig()

        self.should_dump_processes = self.profile_dump_config.dump_processes
        self.symlink_duplicates = self.profile_dump_config.symlink_duplicates
        self.delete_missing = self.profile_dump_config.delete_missing
        self.organize_by_groups = self.profile_dump_config.organize_by_groups
        self.only_top_level_calcs = self.profile_dump_config.only_top_level_calcs
        self.only_top_level_workflows = self.profile_dump_config.only_top_level_workflows
        self.filter_nodes_by_last_dump_time = self.profile_dump_config.filter_nodes_by_last_dump_time

        self.group_nodes: list[str] | None = None
        self.processes_to_dump: ProcessContainer | None = None
        self.processes_to_delete: ProcessContainer | None = None

    @cached_property
    def group_nodes(self) -> list[str]:
        """Property to hold the nodes of the group.

        :return: List of collection node UUIDs.
        """
        # ipdb.set_trace()
        if self.group:
            nodes = self._get_group_nodes()
        else:
            nodes = self._get_no_group_nodes()

        if self.filter_nodes_by_last_dump_time:
            nodes = do_filter_nodes(nodes=nodes, last_dump_time=self.last_dump_time)

        return nodes

    def _get_group_nodes(self) -> list[str]:
        assert self.group is not None, "`self.group` shouldn't be None at this stage."
        return [n.uuid for n in self.group.nodes]

    @cached_property
    def processes_to_dump(self) -> ProcessContainer:
        """Get the processes to dump from the collection of nodes.

        Only re-evaluates the processes, if not already set.

        :return: Instance of a ``ProcessesToDumpContainer``, that holds the selected calculations and workflows.
        """

        return self._get_processes_to_dump()

    def _get_processes_to_dump(self) -> ProcessContainer:
        """Retrieve the processeses from the collection nodes.

        Depending on the attributes of the ``CollectionDumper``, this method takes care of only selecting top-level
        workflows and calculations if they are not part of a workflow. This requires to use the actual ORM entities,
        rather than UUIDs, as the ``.caller``s have to be checked. In addition, sub-calculations

        :return: Instance of a ``ProcessesToDumpContainer``, that holds the selected calculations and workflows.
        """

        ipdb.set_trace()
        if not self.group_nodes:
            raise Exception('Debugging')
            return ProcessContainer(calculations=[], workflows=[])

        # Better than: `nodes = [orm.load_node(n) for n in self.collection_nodes]`
        # As the list comprehension fetches each node from the DB individually
        nodes_orm = orm.QueryBuilder().append(orm.Node, filters={'uuid': {'in': self.group_nodes}}).all(flat=True)

        if self.profile_dump_config.only_top_level_workflows:
            workflows = [node for node in nodes_orm if isinstance(node, orm.WorkflowNode) and node.caller is None]
        else:
            workflows = [node for node in nodes_orm if isinstance(node, orm.WorkflowNode)]

        if self.profile_dump_config.only_top_level_calcs:
            calculations = [node for node in nodes_orm if isinstance(node, orm.CalculationNode) and node.caller is None]
        else:
            calculations = [node for node in nodes_orm if isinstance(node, orm.CalculationNode)]

            # Get sub-calculations that were called by workflows but which might themselves not be directly contained in
            # the collection
            called_calculations = []
            for workflow in workflows:
                called_calculations += [
                    node for node in workflow.called_descendants if isinstance(node, orm.CalculationNode)
                ]

            # Convert to set to avoid duplicates
            calculations = list(set(calculations + called_calculations))

        # Use this small helper class rather than returning a dictionary for access via dot-notation
        return ProcessContainer(
            calculations=calculations,
            workflows=workflows,
        )

    @cached_property
    def processes_to_delete(self) -> ProcessContainer:
        """Get the processes to dump from the collection of nodes.

        Only re-evaluates the processes, if not already set.

        :return: Instance of a ``ProcessesToDumpContainer``, that holds the selected calculations and workflows.
        """
        if not self.delete_missing:
            return ProcessContainer(calculations=[], workflows=[])
        return self._get_processes_to_delete()

    def _get_processes_to_delete(self) -> ProcessContainer:
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

    def _get_no_group_nodes(self) -> list[str]:
        """Obtain nodes in the profile that are not part of any group.

        :return: List of UUIDs of selected nodes.
        """

        profile_groups = cast(list[orm.Group], orm.QueryBuilder().append(orm.Group).all(flat=True))
        profile_nodes = cast(
            list[str],
            orm.QueryBuilder().append(orm.ProcessNode, project=['uuid']).all(flat=True),
        )

        nodes_in_groups: list[str] = [node.uuid for group in profile_groups for node in group.nodes]

        # Need to expand here also with the called_descendants of `WorkflowNodes`, otherwise the called
        # `CalculationNode`s for `WorkflowNode`s that are part of a group are dumped twice
        # Get the called descendants of WorkflowNodes within the nodes_in_groups list
        sub_nodes_in_groups: list[str] = [
            node.uuid
            for n in nodes_in_groups
            # if isinstance((workflow_node := orm.load_node(n)), orm.WorkflowNode)
            if isinstance((workflow_node := orm.load_node(n)), orm.ProcessNode)
            for node in workflow_node.called_descendants
        ]

        nodes_in_groups += sub_nodes_in_groups

        no_group_nodes: list[str] = [
            profile_node for profile_node in profile_nodes if profile_node not in nodes_in_groups
        ]
        if self.filter_nodes_by_last_dump_time:
            no_group_nodes = do_filter_nodes(nodes=no_group_nodes, last_dump_time=self.last_dump_time)

        return no_group_nodes

    # def _get_no_group_processes(self) -> list[str]:
    #     """Obtain nodes in the profile that are not part of any group.

    #     :return: List of UUIDs of selected nodes.
    #     """

    #     profile_groups = cast(list[orm.Group], orm.QueryBuilder().append(orm.Group).all(flat=True))
    #     profile_processes = cast(
    #         list[str],
    #         orm.QueryBuilder().append(orm.ProcessNode, project=['uuid']).all(flat=True),
    #     )

    #     nodes_in_groups: list[str] = [node.uuid for group in profile_groups for node in group.nodes]

    #     # Need to expand here also with the called_descendants of `WorkflowNodes`, otherwise the called
    #     # `CalculationNode`s for `WorkflowNode`s that are part of a group are dumped twice
    #     # Get the called descendants of WorkflowNodes within the nodes_in_groups list
    #     sub_nodes_in_groups: list[str] = [
    #         node.uuid
    #         for n in nodes_in_groups
    #         # if isinstance((workflow_node := orm.load_node(n)), orm.WorkflowNode)
    #         if isinstance((workflow_node := orm.load_node(n)), orm.ProcessNode)
    #         for node in workflow_node.called_descendants
    #     ]

    #     nodes_in_groups += sub_nodes_in_groups

    #     process_nodes: list[str] = [
    #         profile_node for profile_node in profile_processes if profile_node not in nodes_in_groups
    #     ]
    #     process_nodes = filter_nodes_last_dump_time(nodes=process_nodes, last_dump_time=self.last_dump_time)

    #     return process_nodes

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

        sub_path = self.dump_parent_path / self.dump_sub_path / NodeDumpKeyMapper.get_key_from_node(node=processes[0])
        # sub_path = Path(NodeDumpKeyMapper.get_key_from_node(node=next(iter(processes))))
        sub_path.mkdir(exist_ok=True, parents=True)

        logger_attr = NodeDumpKeyMapper.get_key_from_node(node=next(iter(processes)))
        # ! `getattr` gives a reference to the actual object, thus I can update the store directly
        current_store = getattr(self.dump_logger.log, logger_attr)

        process_dumper = ProcessDumper(
            dump_parent_path=sub_path.parent,
            dump_sub_path=sub_path.name,
            last_dump_time=self.last_dump_time,
            base_dump_config=self.base_dump_config,
            process_dump_config=self.process_dump_config,
            dump_logger=self.dump_logger,
        )

        for process in processes:
            process_dump_path = sub_path / generate_process_default_dump_path(process_node=process, prefix=None)

            if self.profile_dump_config.symlink_duplicates and process.uuid in current_store.entries.keys():
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

    def dump(self, output_path: Path | None = None) -> None:
        """Top-level method that actually performs the dumping of the AiiDA data for the collection.

        :return: None
        """

        if not output_path:
            output_path = self.dump_parent_path
        if not output_path.is_absolute():
            output_path /= self.dump_parent_path
        self.dump_parent_path = output_path

        self.dump_parent_path.mkdir(exist_ok=True, parents=True)
        group_nodes: list[str] = self.group_nodes
        collection_processes: ProcessContainer = self.processes_to_dump

        # ipdb.set_trace()

        if not self.processes_to_dump.is_empty:
            # First, dump workflows, then calculations
            if len(collection_processes.workflows) > 0:
                self._dump_processes(processes=collection_processes.workflows)
            if len(collection_processes.calculations) > 0:
                self._dump_processes(processes=collection_processes.calculations)

    # @property
    # def processes_to_delete(self): ...
