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
from functools import cached_property
from pathlib import Path
from typing import TYPE_CHECKING, NamedTuple, TypeVar

from aiida import orm
from aiida.common.log import AIIDA_LOGGER
from aiida.tools.dumping.base import BaseDumper
from aiida.tools.dumping.logger import DumpLog, DumpLogger
from aiida.tools.dumping.process import ProcessDumper
from aiida.tools.dumping.utils import filter_by_last_dump_time

if TYPE_CHECKING:
    from collections.abc import Sequence

    from aiida.tools.dumping.logger import DumpDict

T = TypeVar('T', bound='orm.ProcessNode')


logger = AIIDA_LOGGER.getChild('tools.dumping')


class ProcessesToDump(NamedTuple):
    calculations: Sequence[orm.CalculationNode]
    workflows: Sequence[orm.WorkflowNode]


class CollectionDumper:
    def __init__(
        self,
        base_dumper: BaseDumper | None = None,
        process_dumper: ProcessDumper | None = None,
        dump_logger: DumpLogger | None = None,
        collection: orm.Group | str | list[str] | None = None,
        deduplicate: bool = True,
        output_path: Path | None = None,
        processes_to_dump: ProcessesToDump | None = None,
    ):
        self.deduplicate = deduplicate

        # Collection could be a Group or a list of nodes
        if isinstance(collection, str):
            try:
                collection = orm.load_group(collection)
            except:
                raise

        self.collection = collection

        self.base_dumper = base_dumper or BaseDumper()
        self.process_dumper = process_dumper or ProcessDumper()
        self.dump_logger = dump_logger or DumpLogger(dump_parent_path=self.base_dumper.dump_parent_path)

        # Properly set the `output_path` attribute
        if output_path is not None:
            self.output_path = output_path
        else:
            self.output_path = Path.cwd()

    @cached_property
    def nodes(self) -> list[str]:
        return self._get_nodes()

    def _get_nodes(self) -> list[str]:
        nodes: list[str] | None = None
        if isinstance(self.collection, orm.Group):
            nodes = [n.uuid for n in self.collection.nodes]
        elif isinstance(self.collection, list) and len(self.collection) > 0:
            if all(isinstance(n, str) for n in self.collection):
                nodes = self.collection
            else:
                msg = 'A collection of nodes must be passed via their UUIDs.'
                raise TypeError(msg)
        else:
            nodes = []

        filtered_nodes = filter_by_last_dump_time(nodes=nodes, last_dump_time=self.base_dumper.last_dump_time)
        return filtered_nodes

    @cached_property
    def processes_to_dump(self) -> ProcessesToDump:
        return self._get_processes_to_dump()

    def _get_processes_to_dump(self) -> ProcessesToDump:
        nodes = [orm.load_node(n) for n in self.nodes]
        workflows = [node for node in nodes if isinstance(node, orm.WorkflowNode)]
        calculations = [node for node in nodes if isinstance(node, orm.CalculationNode)]

        # Make sure that only top-level workflows are dumped in their own directories when de-duplcation is enabled
        if self.deduplicate:
            workflows = [workflow for workflow in workflows if workflow.caller is None]

        else:
            # If no deduplication, also sub-calculations that were called by workflows of the group, and which are not
            # contained in the group.nodes directly are being dumped explicitly
            called_calculations = []
            for workflow in workflows:
                called_calculations += [
                    node for node in workflow.called_descendants if isinstance(node, orm.CalculationNode)
                ]

            calculations += called_calculations

        return ProcessesToDump(
            calculations=calculations,
            workflows=workflows,
        )

    def should_dump_processes(self) -> bool:
        # if self.processes_to_dump is None:
        #     self._get_processes_to_dump()
        return (len(self.processes_to_dump.calculations) + len(self.processes_to_dump.workflows)) > 0

    def _dump_calculations(self, calculations: Sequence[orm.CalculationNode]) -> None:
        calculations_path = self.output_path / 'calculations'
        dumped_calculations = {}

        for calculation in calculations:
            calculation_dumper = self.process_dumper

            calculation_dump_path = calculations_path / calculation_dumper._generate_default_dump_path(
                process_node=calculation, prefix=None
            )

            # This is handled in the get_processes method: `if calculation.caller is None:`
            calculation_dumper._dump_calculation(calculation_node=calculation, output_path=calculation_dump_path)

            dumped_calculations[calculation.uuid] = DumpLog(
                path=calculation_dump_path,
                time=datetime.now().astimezone(),
            )

        self.dump_logger.update_calculations(new_calculations=dumped_calculations)

    def _dump_workflows(self, workflows: Sequence[orm.WorkflowNode]) -> None:
        workflow_path: Path = self.output_path / 'workflows'
        dumped_workflows: dict[str, DumpLog] = {}

        workflow_path.mkdir(exist_ok=True, parents=True)

        for workflow in workflows:
            workflow_dumper: ProcessDumper = self.process_dumper

            workflow_dump_path: Path = workflow_path / workflow_dumper._generate_default_dump_path(
                process_node=workflow, prefix=None
            )

            logged_workflows: DumpDict = self.dump_logger.get_log()['workflows']

            # Symlink here, if deduplication enabled and workflow was already dumped
            if self.deduplicate and workflow in logged_workflows.keys():
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
        self.output_path.mkdir(exist_ok=True, parents=True)
        collection_processes: ProcessesToDump = self._get_processes_to_dump()

        if len(collection_processes.calculations) > 0:
            self._dump_calculations(calculations=collection_processes.calculations)
        if len(collection_processes.workflows) > 0:
            self._dump_workflows(workflows=collection_processes.workflows)
