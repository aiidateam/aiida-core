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

import os
from datetime import datetime
from pathlib import Path

from aiida import orm
from aiida.common.log import AIIDA_LOGGER
from aiida.tools.dumping.base import BaseDumper
from aiida.tools.dumping.config import BaseDumpConfig, ProfileDumpConfig
from aiida.tools.dumping.logger import DumpLog, DumpLogger
from aiida.tools.dumping.process import ProcessDumper
from aiida.tools.dumping.utils import (
    NodeDumpKeyMapper,
    ProcessesToDumpContainer,
    filter_nodes_last_dump_time,
    load_given_group,
)

logger = AIIDA_LOGGER.getChild('tools.dumping')


class CollectionDumper(BaseDumper):
    """Class to handle dumping of a collection of AiiDA ORM entities."""

    def __init__(
        self,
        base_dump_config: BaseDumpConfig | None = None,
        dump_logger: DumpLogger | None = None,
        group: orm.Group | str | None = None,
        collection_nodes: list[str] | None = None,
        # Need to pass the `profile_dump_config` to have access to some of the top-level settings
        profile_dump_config: ProfileDumpConfig | None = None,
        process_dumper: ProcessDumper | None = None,
    ):
        """Initialize the CollectionDumper.

        :param base_dump_config: Base dumper instance or None (gets instantiated).
        :param dump_logger: Logger for the dumping (gets instantiated).
        :param group: AiiDA group of which the nodes should be dumped.
        :param collection_nodes: List of AiiDA nodes that should be dumped, given by their UUIDs.
        :param process_dumper: Process dumper instance or None (gets instantiated).
        :param processes_to_dump: Optional precomputed processes to dump.
        """

        super().__init__(base_dump_config=base_dump_config, dump_logger=dump_logger)

        self._collection_nodes: list[str] = []  # Explicit type annotation

        if group is not None and collection_nodes is not None:
            msg = 'Cannot provide both, a group, and a collection of nodes.'
            raise Exception(msg)

        elif group is not None:
            self.group = load_given_group(group)
            if self.group:
                self._collection_nodes = [n.uuid for n in self.group.nodes]

        elif collection_nodes is not None:
            if any([not isinstance(n, str) for n in collection_nodes]):
                msg = 'Currently, passing a collection of nodes is only supported via their UUID.'
                raise TypeError(msg)
            self._collection_nodes = collection_nodes

        else:
            self.group = None

        # ? If also using composition for BaseDumpConfig, rather than inheriting from BaseDumper
        # self.base_dump_config = base_dump_config or BaseDumpConfig()

        self.profile_dump_config = profile_dump_config or ProfileDumpConfig()
        self.process_dumper = process_dumper or ProcessDumper()

        self._processes_to_dump: ProcessesToDumpContainer | None = None

    @property
    def collection_nodes(self) -> list[str]:
        """Property to hold the collection nodes.

        Takes care of respecting the ``incremental`` attribute, and filtering by ``last_dump_time``.

        :return: List of collection node UUIDs.
        """
        if self.incremental and self.last_dump_time:
            self._collection_nodes = filter_nodes_last_dump_time(
                self._collection_nodes, last_dump_time=self.last_dump_time
            )

        return self._collection_nodes

    @property
    def processes_to_dump(self) -> ProcessesToDumpContainer:
        """Get the processes to dump from the collection of nodes.

        Only re-evaluates the processes, if not already set.

        :return: Instance of a ``ProcessesToDumpContainer``, that holds the selected calculations and workflows.
        """
        if not self._processes_to_dump:
            self._processes_to_dump = self._get_processes_to_dump()
        return self._processes_to_dump

    def _get_processes_to_dump(self) -> ProcessesToDumpContainer:
        """Retrieve the processeses from the collection nodes.

        Depending on the attributes of the ``CollectionDumper``, this method takes care of only selecting top-level
        workflows and calculations if they are not part of a workflow. This requires to use the actual ORM entities,
        rather than UUIDs, as the ``.caller``s have to be checked. In addition, sub-calculations

        :return: Instance of a ``ProcessesToDumpContainer``, that holds the selected calculations and workflows.
        """

        if not self.collection_nodes:
            return ProcessesToDumpContainer(calculations=[], workflows=[])

        # Better than: `nodes = [orm.load_node(n) for n in self.collection_nodes]`
        # As the list comprehension fetches each node from the DB individually
        nodes_orm = orm.QueryBuilder().append(orm.Node, filters={'uuid': {'in': self.collection_nodes}}).all(flat=True)

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
        return ProcessesToDumpContainer(
            calculations=calculations,
            workflows=workflows,
        )

    def _dump_processes(self, processes: list[orm.CalculationNode] | list[orm.WorkflowNode]) -> None:
        """Dump a list of AiiDA calculations or workflows to disk.

        :param processes: List of AiiDA calculations or workflows from the ``ProcessesToDumpContainer``.
        """

        if len(list(processes)) == 0:
            return

        # TODO: Only allow for "pure" sequences of Calculation- or WorkflowNodes, or also mixed?
        # TODO: If the latter possibly also have directory creation in the loop
        sub_path = self.dump_parent_path / NodeDumpKeyMapper.get_key_from_node(node=next(iter(processes)))
        sub_path.mkdir(exist_ok=True, parents=True)

        logger_attr = NodeDumpKeyMapper.get_key_from_node(node=next(iter(processes)))
        # ! `getattr` gives a reference to the actual object, thus I can update the store directly
        current_store = getattr(self.dump_logger.log, logger_attr)

        process_dumper = self.process_dumper

        for process in processes:
            process_dump_path = sub_path / process_dumper._generate_default_dump_path(process_node=process, prefix=None)

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
        collection_processes: ProcessesToDumpContainer = self._get_processes_to_dump()

        if not self.processes_to_dump.is_empty:
            # First, dump workflows, then calculations
            if len(collection_processes.workflows) > 0:
                self._dump_processes(processes=collection_processes.workflows)
            if len(collection_processes.calculations) > 0:
                self._dump_processes(processes=collection_processes.calculations)
