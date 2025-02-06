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
from typing import TYPE_CHECKING, TypeVar, cast

from aiida import orm
from aiida.common.log import AIIDA_LOGGER
from aiida.tools.dumping.base import BaseDumper
from aiida.tools.dumping.logger import DumpLog, DumpLogger
from aiida.tools.dumping.process import ProcessDumper
from aiida.tools.dumping.utils import filter_by_last_dump_time

if TYPE_CHECKING:
    from collections.abc import Sequence

T = TypeVar('T', bound='orm.ProcessNode')


logger = AIIDA_LOGGER.getChild('tools.dumping')


class CollectionDumper:
    def __init__(
        self,
        base_dumper: BaseDumper | None = None,
        process_dumper: ProcessDumper | None = None,
        dump_logger: DumpLogger | None = None,
        collection: orm.Group | str | list[str] | None = None,
        deduplicate: bool = True,
        output_path: Path | None = None,
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

    def _should_dump_processes(self, nodes: list[str] | None = None) -> bool:
        test_nodes = nodes or self.nodes
        return len([node for node in test_nodes if isinstance(orm.load_node(node), orm.ProcessNode)]) > 0

    def _get_processes(self) -> dict[str, Sequence[orm.ProcessNode]]:
        nodes = [orm.load_node(n) for n in self.nodes]
        workflows = [node for node in nodes if isinstance(node, orm.WorkflowNode)]

        # Make sure that only top-level workflows are dumped in their own directories when de-duplcation is enabled
        if self.deduplicate:
            workflows = [workflow for workflow in workflows if workflow.caller is None]

        # Also need to obtain sub-calculations that were called by workflows of the group
        # These are not contained in the group.nodes directly
        called_calculations = []
        for workflow in workflows:
            called_calculations += [
                node for node in workflow.called_descendants if isinstance(node, orm.CalculationNode)
            ]

        calculations = [node for node in nodes if isinstance(node, orm.CalculationNode)] + called_calculations
        return {
            'calculations': cast(Sequence[orm.ProcessNode], calculations),
            'workflows': cast(Sequence[orm.ProcessNode], workflows),
        }
        # return {'calculations': calculations, 'workflows': workflows}

    def _dump_calculations(self, calculations: Sequence[orm.CalculationNode]) -> None:
        if len(calculations) == 0:
            return
        calculations_path = self.output_path / 'calculations'
        dumped_calculations = {}

        for calculation in calculations:
            calculation_dumper = self.process_dumper

            calculation_dump_path = calculations_path / calculation_dumper._generate_default_dump_path(
                process_node=calculation, prefix=None
            )

            if calculation.caller is None:
                calculation_dumper._dump_calculation(
                    calculation_node=cast(orm.CalculationNode, calculation), output_path=calculation_dump_path
                )

                dumped_calculations[calculation.uuid] = DumpLog(
                    path=calculation_dump_path,
                    time=datetime.now().astimezone(),
                )

        self.dump_logger.update_calculations(dumped_calculations)

    def _dump_workflows(self, workflows: Sequence[orm.WorkflowNode]) -> None:
        if len(workflows) == 0:
            return
        workflow_path = self.output_path / 'workflows'
        workflow_path.mkdir(exist_ok=True, parents=True)
        dumped_workflows = {}

        for workflow in workflows:
            workflow_dumper = self.process_dumper

            workflow_dump_path = workflow_path / workflow_dumper._generate_default_dump_path(
                process_node=workflow, prefix=None
            )

            logged_workflows = self.dump_logger.get_log()['workflows']

            if self.deduplicate and workflow in logged_workflows.keys():
                os.symlink(
                    src=logged_workflows[workflow.uuid].path,
                    dst=workflow_dump_path,
                )
            else:
                workflow_dumper._dump_workflow(
                    workflow_node=cast(orm.WorkflowNode, workflow),
                    output_path=workflow_dump_path,
                )

                dumped_workflows[workflow.uuid] = DumpLog(
                    path=workflow_dump_path,
                    time=datetime.now().astimezone(),
                )

        self.dump_logger.update_workflows(dumped_workflows)

    def dump(self) -> None:
        self.output_path.mkdir(exist_ok=True, parents=True)
        collection_processes = self._get_processes()
        self._dump_calculations(calculations=collection_processes['calculations'])
        self._dump_workflows(workflows=collection_processes['workflows'])
