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
from typing import TYPE_CHECKING, NamedTuple

from aiida import orm
from aiida.common.exceptions import NotExistent
from aiida.common.log import AIIDA_LOGGER
from aiida.tools.dumping.config import BaseDumpConfig, ProfileDumpConfig
from aiida.tools.dumping.logger import DumpLog, DumpLogger
from aiida.tools.dumping.process import ProcessDumper
from aiida.tools.dumping.utils import NodeDumpMapper, extend_calculations, filter_by_last_dump_time

if TYPE_CHECKING:
    from collections.abc import Collection, Sequence


logger = AIIDA_LOGGER.getChild('tools.dumping')


class ProcessesDumpContainer(NamedTuple):
    calculations: Sequence[orm.CalculationNode]
    workflows: Sequence[orm.WorkflowNode]

    @property
    def is_empty(self) -> bool:
        """Check if there are any processes to dump."""
        return len(self.calculations) == 0 and len(self.workflows) == 0


class CollectionDumper:
    """Class to handle dumping of a collection of AiiDA ORM entities."""

    def __init__(
        self,
        # TODO: Refactor here to different arguments: Group, and collection_nodes
        collection: orm.Group | str | Collection[str],
        profile_dump_config: ProfileDumpConfig | None = None,
        base_dump_config: BaseDumpConfig | None = None,
        process_dumper: ProcessDumper | None = None,
        dump_logger: DumpLogger | None = None,
        output_path: Path | None = None,
    ):
        """Initialize the CollectionDumper.

        :param collection: The collection of AiiDA ORM entities to be dumped, either a group, group label, or list of
        :param base_dump_config: Base dumper instance or None (gets instantiated).
        :param process_dumper: Process dumper instance or None (gets instantiated).
        :param dump_logger: Logger for the dumping (gets instantiated).
        :param output_path: The parent output path for dumping the collection nodes.
        :param processes_to_dump: Optional precomputed processes to dump.
        """

        self.collection = self._validate_collection(collection)

        self.base_dump_config = base_dump_config or BaseDumpConfig()
        self.process_dumper = process_dumper or ProcessDumper()
        self.dump_logger = dump_logger or DumpLogger(dump_parent_path=self.base_dump_config.dump_parent_path)

        self.output_path = output_path or Path.cwd()

        self.profile_dump_config = profile_dump_config or ProfileDumpConfig()

        self._collection_nodes: Collection[str] | None = None
        self._processes_to_dump: ProcessesDumpContainer | None = None

    def _validate_collection(
        self, collection: orm.Group | str | Collection[str] | Collection[int]
    ) -> orm.Group | Collection[str]:
        """Validate the given collection identifier.

        :param collection: The input collection to validate.
        :return: The validated collection.
        :raises NotExistent: If no ``orm.Group`` can be loaded for a given label.
        :raises ValueError: If no list of integers or strings to identify nodes is passed.
        """

        if isinstance(collection, str):
            try:
                return orm.load_group(collection)
            except Exception as exc:
                msg = f'Could not load group: {collection}.'
                raise NotExistent(msg) from exc

        elif isinstance(collection, orm.Group):
            return collection

        elif isinstance(collection, list):
            if all(isinstance(n, str) for n in collection):
                return collection

            elif all(isinstance(n, int) for n in collection):
                msg = 'Passing node collections via their PK not yet supported.'
                raise ValueError(msg)

            else:
                msg = 'Mixing identifiers or passing other types not supported'
                raise ValueError(msg)

        elif isinstance(collection, list) and all(isinstance(n, int) for n in collection):
            return collection

        else:
            msg = f'{collection} is an invalid collection.'
            raise ValueError(msg)

    @property
    def collection_nodes(self) -> Collection[str]:
        """Return collection nodes.

        :return: List of collection node identifiers.
        """
        if self._collection_nodes is None:
            self._collection_nodes = self._get_collection_nodes()
        return self._collection_nodes

    def _get_collection_nodes(self) -> Collection[str]:
        """Retrieve the node UUIDs from the collection, filtered by the last dump time, if for incremental dumping.

        :return: List of node UUIDs.
        """
        if not self.collection:
            return []

        if isinstance(self.collection, orm.Group):
            nodes: Collection[str] = [n.uuid for n in self.collection.nodes]
        else:
            nodes = self.collection

        if self.base_dump_config.incremental and self.base_dump_config.last_dump_time:
            nodes = filter_by_last_dump_time(nodes, last_dump_time=self.base_dump_config.last_dump_time)

        return nodes

    @property
    def processes_to_dump(self) -> ProcessesDumpContainer:
        """Get the processes to dump from the collection of nodes.

        :return: Instance of the ``ProcessesToDump`` class containing the selected calculations and workflows.
        """
        if not self._processes_to_dump:
            self._processes_to_dump = self._get_processes_to_dump()
        return self._processes_to_dump

    def _get_processes_to_dump(self) -> ProcessesDumpContainer:
        """Retrieve the processeses from the collection nodes.

        If deduplication is selected, this method takes care of only dumping top-level workflows and only dump
        calculations in their own designated directories if they are not part of a workflow.

        :return: Instance of the ``ProcessesToDump`` class containing the selected calculations and workflows.
        """

        # Deduplication is already handled in the ``get_processes`` method, where PKs/UUIDs are used, rather than AiiDA
        # ORM entities as here. Specifically, calculations that are part of a workflow are not dumpid in their own,
        # dedicated directory if they are part of a workflow.

        if not self.collection_nodes:
            return ProcessesDumpContainer(calculations=[], workflows=[])

        # Better than: `nodes = [orm.load_node(n) for n in self.collection_nodes]`
        # As the list comprehension fetches each node from the DB individually
        nodes_orm = orm.QueryBuilder().append(orm.Node, filters={'uuid': {'in': self.collection_nodes}}).all(flat=True)

        workflows = [node for node in nodes_orm if isinstance(node, orm.WorkflowNode) and node.caller is None]
        calculations = [node for node in nodes_orm if isinstance(node, orm.CalculationNode) and node.caller is None]

        if self.profile_dump_config.extra_calc_dirs:
            calculations = extend_calculations(
                profile_dump_config=self.profile_dump_config, calculations=calculations, workflows=workflows
            )

        return ProcessesDumpContainer(
            calculations=calculations,
            workflows=workflows,
        )

    def _dump_processes(self, processes: Sequence[orm.CalculationNode] | Sequence[orm.WorkflowNode]) -> None:
        """Dump a collection of processes."""

        if len(processes) == 0:
            return

        # TODO: Only allow for "pure" sequences of Calculation- or WorkflowNodes, or also mixed?
        # TODO: If the latter possibly also have directory creation in the loop
        sub_path = self.output_path / NodeDumpMapper.get_directory(node=processes[0])
        sub_path.mkdir(exist_ok=True, parents=True)

        logger_attr = NodeDumpMapper.get_logger_attr(node=processes[0])
        # ! `getattr` gives a reference to the object, thus I can update the store directly
        current_store = getattr(self.dump_logger.log, logger_attr)

        # breakpoint()

        for process in processes:
            process_dumper = self.process_dumper

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

    def dump(self) -> None:
        """Top-level method that actually performs the dumping of the AiiDA data for the collection.

        :return: None
        """

        self.output_path.mkdir(exist_ok=True, parents=True)
        collection_processes: ProcessesDumpContainer = self._get_processes_to_dump()
        # breakpoint()

        if not self.processes_to_dump.is_empty:
            # self._dump_processes(processes=collection_processes)

            # First, dump workflows, then calculations
            if len(collection_processes.workflows) > 0:
                self._dump_processes(processes=collection_processes.workflows)
            if len(collection_processes.calculations) > 0:
                self._dump_processes(processes=collection_processes.calculations)
