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
from aiida.tools.dumping.base import BaseDumper
from aiida.tools.dumping.config import ProfileDumpConfig
from aiida.tools.dumping.logger import DumpLog, DumpLogger
from aiida.tools.dumping.process import ProcessDumper
from aiida.tools.dumping.utils import filter_by_last_dump_time, extend_calculations

if TYPE_CHECKING:
    from collections.abc import Sequence

    from aiida.tools.dumping.logger import DumpDict


logger = AIIDA_LOGGER.getChild('tools.dumping')


class ProcessesToDump(NamedTuple):
    calculations: Sequence[orm.CalculationNode]
    workflows: Sequence[orm.WorkflowNode]

    @property
    def is_empty(self) -> bool:
        """Check if there are any processes to dump."""
        return len(self.calculations) == 0 and len(self.workflows) == 0


# @dataclass
# class CollectionDumpConfig:
#     dump_processes: bool = True
#     symlink_duplicates: bool = True
#     delete_missing: bool = False
#     extra_calc_dirs: bool = False
#     organize_by_groups: bool = True


class CollectionDumper:
    """Class to handle dumping of a collection of AiiDA ORM entities."""

    def __init__(
        self,
        collection: orm.Group | str | Sequence[str] | Sequence[int],
        profile_dump_config: ProfileDumpConfig | None = None,
        base_dumper: BaseDumper | None = None,
        process_dumper: ProcessDumper | None = None,
        dump_logger: DumpLogger | None = None,
        output_path: Path | None = None,
    ):
        """Initialize the CollectionDumper.

        :param collection: The collection of AiiDA ORM entities to be dumped, either a group, group label, or list of
        :param base_dumper: Base dumper instance or None (gets instantiated).
        :param process_dumper: Process dumper instance or None (gets instantiated).
        :param dump_logger: Logger for the dumping (gets instantiated).
        :param output_path: The parent output path for dumping the collection nodes.
        :param processes_to_dump: Optional precomputed processes to dump.
        """

        self.collection = self._validate_collection(collection)

        self.base_dumper = base_dumper or BaseDumper()
        self.process_dumper = process_dumper or ProcessDumper()
        self.dump_logger = dump_logger or DumpLogger(dump_parent_path=self.base_dumper.dump_parent_path)

        self.output_path = output_path or Path.cwd()

        self.profile_dump_config = profile_dump_config or ProfileDumpConfig()

        self._collection_nodes: Sequence[str] | Sequence[int] | None = None
        self._processes_to_dump: ProcessesToDump | None = None

    def _validate_collection(
        self, collection: orm.Group | str | Sequence[str] | Sequence[int]
    ) -> orm.Group | Sequence[str] | Sequence[int]:
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
        if (isinstance(collection, list) and all(isinstance(n, (str, int)) for n in collection)) or isinstance(
            collection, orm.Group
        ):
            return collection

        else:
            msg = f'{collection} is an invalid collection.'
            raise ValueError(msg)

    @property
    def collection_nodes(self) -> Sequence[str] | Sequence[int]:
        """Return collection nodes.

        :return: List of collection node identifiers.
        """
        if self._collection_nodes is None:
            self._collection_nodes = self._get_collection_nodes()
        return self._collection_nodes

    def _get_collection_nodes(self) -> Sequence[str] | Sequence[int]:
        """Retrieve the node ``PK``s/``UUID``s from the collection, filtered by the last dump time, if incremental
        dumping is selected.

        :return: List of node identifiers.
        """
        if not self.collection:
            return []

        nodes = [n.uuid for n in self.collection.nodes] if isinstance(self.collection, orm.Group) else self.collection

        if self.base_dumper.incremental and self.base_dumper.last_dump_time:
            nodes = filter_by_last_dump_time(nodes, last_dump_time=self.base_dumper.last_dump_time)

        return nodes

    @property
    def processes_to_dump(self) -> ProcessesToDump:
        """Get the processes to dump from the collection of nodes.

        :return: Instance of the ``ProcessesToDump`` class containing the selected calculations and workflows.
        """
        if not self._processes_to_dump:
            self._processes_to_dump = self._get_processes_to_dump()
        return self._processes_to_dump

    def _get_processes_to_dump(self) -> ProcessesToDump:
        """Retrieve the processeses from the collection nodes.

        If deduplication is selected, this method takes care of only dumping top-level workflows and only dump
        calculations in their own designated directories if they are not part of a workflow.

        :return: Instance of the ``ProcessesToDump`` class containing the selected calculations and workflows.
        """

        if not self.collection_nodes:
            return ProcessesToDump(calculations=[], workflows=[])

        # Better than: `nodes = [orm.load_node(n) for n in self.collection_nodes]`
        # As the list comprehension fetches each node from the DB individually
        nodes_orm = orm.QueryBuilder().append(orm.Node, filters={'uuid': {'in': self.collection_nodes}}).all(flat=True)

        workflows = [node for node in nodes_orm if isinstance(node, orm.WorkflowNode) and node.caller is None]
        calculations = [node for node in nodes_orm if isinstance(node, orm.CalculationNode) and node.caller is None]

        if self.profile_dump_config.extra_calc_dirs:
            calculations = extend_calculations(profile_dump_config=self.profile_dump_config, calculations=calculations, workflows=workflows)

        return ProcessesToDump(
            calculations=calculations,
            workflows=workflows,
        )

    def _dump_calculations(self, calculations: Sequence[orm.CalculationNode]) -> None:
        """Dump a collection of calculations.

        Deduplication is already handled in the ``get_processes`` method, where PKs/UUIDs are used, rather than AiiDA
        ORM entities as here. Specifically, calculations that are part of a workflow are not dumpid in their own,
        dedicated directory if they are part of a workflow.

        :param calculations: Sequence of ``orm.CalculationNode``s
        :return: None
        """

        calculations_path = self.output_path / 'calculations'
        dumped_calculations: dict[str, DumpLog] = {}

        logged_calculations: DumpDict = self.dump_logger.get_log()['calculations']

        for calculation in calculations:
            calculation_dumper = self.process_dumper

            calculation_dump_path = calculations_path / calculation_dumper._generate_default_dump_path(
                process_node=calculation, prefix=None
            )

            if self.profile_dump_config.symlink_duplicates and calculation.uuid in logged_calculations.keys():
                calculation_dump_path.parent.mkdir(exist_ok=True, parents=True)
                os.symlink(
                    src=logged_calculations[calculation.uuid].path,
                    dst=calculation_dump_path,
                )

            # This is handled in the get_processes method: `if calculation.caller is None:`
            else:
                # TODO: Don't update the logger with the UUID of a symlinked calculation as keys must be unique
                # TODO: Possibly add another `symlink` attribute to `DumpLog` which can hold a list of symlinks
                calculation_dumper._dump_calculation(calculation_node=calculation, output_path=calculation_dump_path)

                dumped_calculations[calculation.uuid] = DumpLog(
                    path=calculation_dump_path,
                    time=datetime.now().astimezone(),
                )

        self.dump_logger.update_calculations(new_calculations=dumped_calculations)

    def _dump_workflows(self, workflows: Sequence[orm.WorkflowNode]) -> None:
        """Dump a collection of workflows."""
        workflow_path: Path = self.output_path / 'workflows'
        dumped_workflows: dict[str, DumpLog] = {}

        workflow_path.mkdir(exist_ok=True, parents=True)

        logged_workflows: DumpDict = self.dump_logger.get_log()['workflows']

        for workflow in workflows:
            workflow_dumper: ProcessDumper = self.process_dumper

            workflow_dump_path: Path = workflow_path / workflow_dumper._generate_default_dump_path(
                process_node=workflow, prefix=None
            )

            # Symlink here, if deduplication enabled and workflow was already dumped
            if self.profile_dump_config.symlink_duplicates and workflow.uuid in logged_workflows.keys():
                workflow_dump_path.parent.mkdir(exist_ok=True, parents=True)

                os.symlink(
                    src=logged_workflows[workflow.uuid].path,
                    dst=workflow_dump_path,
                )
            else:
                workflow_dumper._dump_workflow(
                    workflow_node=workflow,
                    output_path=workflow_dump_path,
                )

            dumped_workflows[workflow.uuid] = DumpLog(
                path=workflow_dump_path,
                time=datetime.now().astimezone(),
            )

        self.dump_logger.update_workflows(new_workflows=dumped_workflows)

    def dump(self) -> None:
        """Top-level method that actually performs the dumping of the AiiDA data for the collection.

        :return: None
        """

        self.output_path.mkdir(exist_ok=True, parents=True)
        collection_processes: ProcessesToDump = self._get_processes_to_dump()
        # breakpoint()

        if not self.processes_to_dump.is_empty:
            # self._dump_processes(processes=collection_processes)

            # First, dump workflows, then calculations
            if len(collection_processes.workflows) > 0:
                # breakpoint()
                self._dump_workflows(workflows=collection_processes.workflows)
            if len(collection_processes.calculations) > 0:
                # breakpoint()
                self._dump_calculations(calculations=collection_processes.calculations)


# TODO: See, if I can generalize the dump sub-methods
# def _dump_processes(
#     self,
#     # processes: Sequence[orm.CalculationNode | orm.WorkflowNode],
#     processes: Sequence[orm.CalculationNode] | Sequence[orm.WorkflowNode],
# ) -> None:
#     """Dump a collection of calculations or workflows.

#     :param processes: Sequence of ``orm.CalculationNode``s or ``orm.WorkflowNode``s
#     :param process_type: Type of processes, either 'calculations' or 'workflows'
#     :return: None
#     """

#     # From, e.g., 'aiida.workflows:core.arithmetic.multiply_add' to 'workflows
#     if isinstance(processes[0], orm.CalculationNode):
#         process_type_str = 'calculations'
#     elif isinstance(processes[0], orm.WorkflowNode):
#         process_type_str = 'workflows'
#     # else:
#         # breakpoint()
#     # process_type_str = processes[0].process_type.split(':')[0].split('.')[1]
#     process_type_path = self.output_path / process_type_str
#     process_type_path.mkdir(exist_ok=True, parents=True)

#     dumped_processes: dict[str, DumpLog] = {}
#     logged_processes: DumpDict = self.dump_logger.get_log()[process_type_str]

#     # breakpoint()

#     for process in processes:
#         process_dumper = self.process_dumper

#         process_dump_path = process_type_path / process_dumper._generate_default_dump_path(
#             process_node=process, prefix=None
#         )

#         # Target directory already exists, skip this process
#         if process_dump_path.exists():
#             continue

#         else:
#             # Symlink here, if deduplication enabled and process was already dumped
#             # TODO: Possibly check dirs here
#             # TODO: Alternatively have method/endpoint to delete one calculation from the dumping
#             # TODO: Which would also update the log.
#             # Otherwise, one might delete a calculation, maybe because it was wrong, and then it won't be dumped
#             # anymore ever.
#             if self.deduplicate and process.uuid in logged_processes.keys():
#                 try:
#                     os.symlink(
#                         src=logged_processes[process.uuid].path,
#                         dst=process_dump_path,
#                     )
#                 except:
#                     # raise
#                     pass
#                     # breakpoint()
#             else:
#                 if process_type_str == 'calculations':
#                     process_dumper._dump_calculation(calculation_node=process, output_path=process_dump_path)
#                 elif process_type_str == 'workflows':
#                     process_dumper._dump_workflow(
#                         workflow_node=process,
#                         output_path=process_dump_path,
#                     )


#             dumped_processes[process.uuid] = DumpLog(
#                 path=process_dump_path,
#                 time=datetime.now().astimezone(),
#             )

#     # breakpoint()

#     if process_type_str == 'calculations':
#         self.dump_logger.update_calculations(new_calculations=dumped_processes)
#     elif process_type_str == 'workflows':
#         self.dump_logger.update_workflows(new_workflows=dumped_processes)
