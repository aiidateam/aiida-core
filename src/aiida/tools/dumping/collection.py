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
from collections.abc import Iterable
from datetime import datetime
from pathlib import Path
from typing import cast

from aiida import orm
from aiida.common.exceptions import NotExistent
from aiida.common.log import AIIDA_LOGGER
from aiida.tools.dumping.base import BaseDumper
from aiida.tools.dumping.config import BaseDumpConfig, ProfileDumpConfig
from aiida.tools.dumping.logger import DumpLog, DumpLogger
from aiida.tools.dumping.process import ProcessDumper
from aiida.tools.dumping.utils import (
    NodeDumpMapper,
    ProcessesDumpContainer,
    _extend_calculations,
    _filter_by_last_dump_time,
)

logger = AIIDA_LOGGER.getChild('tools.dumping')


class CollectionDumper(BaseDumper):
    """Class to handle dumping of a collection of AiiDA ORM entities."""

    def __init__(
        self,
        group: orm.Group | str | None = None,
        collection_nodes: Iterable[str] | None = None,
        base_dump_config: BaseDumpConfig | None = None,
        # Need to pass that to have access to some of the top-level settings
        profile_dump_config: ProfileDumpConfig | None = None,
        process_dumper: ProcessDumper | None = None,
        dump_logger: DumpLogger | None = None,
        # `kwargs` here if I would like to overwrite some of the `base_dump_config` arguments
    ):
        """Initialize the CollectionDumper.

        :param group:
        :param base_dump_config: Base dumper instance or None (gets instantiated).
        :param process_dumper: Process dumper instance or None (gets instantiated).
        :param dump_logger: Logger for the dumping (gets instantiated).
        :param processes_to_dump: Optional precomputed processes to dump.
        """

        super().__init__(base_dump_config=base_dump_config, dump_logger=dump_logger)

        # breakpoint()

        self._collection_nodes: Iterable[str] = []  # Explicit type annotation

        if group is not None and collection_nodes is not None:
            msg = 'Cannot provide both, group and a collection of nodes.'
            raise Exception(msg)

        elif group is not None:
            self.group = _validate_group(group)
            if self.group:
                self._collection_nodes = [n.uuid for n in self.group.nodes]

        elif collection_nodes is not None:
            self._collection_nodes = _validate_collection_nodes(collection_nodes)

        else:
            self._collection_nodes = []
            # msg = 'Either `group` or `collection_nodes` must be passed.'
            # raise Exception(msg)

        # self.base_dump_config = base_dump_config or BaseDumpConfig()
        self.profile_dump_config = profile_dump_config or ProfileDumpConfig()

        self.process_dumper = process_dumper or ProcessDumper()
        # self.dump_logger = dump_logger or DumpLogger(dump_parent_path=self.dump_parent_path)

        self._processes_to_dump: ProcessesDumpContainer | None = None

    @property
    def collection_nodes(self) -> Iterable[str]:
        """Return collection nodes.

        :return: List of collection node identifiers.
        """
        if self.incremental and self.last_dump_time:
            self._collection_nodes = _filter_by_last_dump_time(
                self._collection_nodes, last_dump_time=self.last_dump_time
            )

        return self._collection_nodes

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

        if self.profile_dump_config.only_top_level_workflows:
            workflows = [node for node in nodes_orm if isinstance(node, orm.WorkflowNode) and node.caller is None]
        else:
            workflows = [node for node in nodes_orm if isinstance(node, orm.WorkflowNode)]

        if self.profile_dump_config.only_top_level_calcs:
            calculations = [node for node in nodes_orm if isinstance(node, orm.CalculationNode) and node.caller is None]
        else:
            calculations = [node for node in nodes_orm if isinstance(node, orm.CalculationNode)]

            # Convert to set to avoid duplicates
            calculations = list(
                set(
                    calculations
                    + _extend_calculations(
                        profile_dump_config=self.profile_dump_config, calculations=calculations, workflows=workflows
                    )
                )
            )

        return ProcessesDumpContainer(
            calculations=calculations,
            workflows=workflows,
        )

    def _dump_processes(self, processes: Iterable[orm.CalculationNode] | Iterable[orm.WorkflowNode]) -> None:
        """Dump a collection of processes."""

        if len(list(processes)) == 0:
            return

        # TODO: Only allow for "pure" sequences of Calculation- or WorkflowNodes, or also mixed?
        # TODO: If the latter possibly also have directory creation in the loop
        assert self.dump_parent_path is not None, "`dump_parent_path` must be set"
        sub_path = self.dump_parent_path / NodeDumpMapper.get_directory(node=next(iter(processes)))
        sub_path.mkdir(exist_ok=True, parents=True)

        logger_attr = NodeDumpMapper.get_logger_attr(node=next(iter(processes)))
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

        assert self.dump_parent_path is not None, "`dump_parent_path` must be set"
        self.dump_parent_path.mkdir(exist_ok=True, parents=True)
        collection_processes: ProcessesDumpContainer = self._get_processes_to_dump()
        # breakpoint()

        if not self.processes_to_dump.is_empty:
            # self._dump_processes(processes=collection_processes)

            # First, dump workflows, then calculations
            if len(collection_processes.workflows) > 0:
                self._dump_processes(processes=collection_processes.workflows)
            if len(collection_processes.calculations) > 0:
                self._dump_processes(processes=collection_processes.calculations)


def _validate_group(group: orm.Group | str | None) -> orm.Group | None:
    """Validate the given group identifier.

    :param group: The group identifier to validate.
    :return: Insance of ``orm.Group``.
    :raises NotExistent: If no ``orm.Group`` can be loaded for a given label.
    """

    if group is None:
        return group

    if isinstance(group, str):
        try:
            return orm.load_group(group)
        # `load_group` raises the corresponding errors
        except NotExistent:
            raise
        except:
            raise

    elif isinstance(group, orm.Group):
        return group


def _validate_collection_nodes(collection_nodes) -> Iterable[str]:
    if isinstance(collection_nodes, Iterable):
        if any([not isinstance(n, str) for n in collection_nodes]):
            msg = 'Currently, passing a collection of nodes is only supported via their UUID.'
            raise TypeError(msg)
    else:
        msg = '`collection_nodes` must be an iterable.'
        raise TypeError(msg)

    collection_nodes = cast(Iterable[str], collection_nodes)

    return collection_nodes
