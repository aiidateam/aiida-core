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

import itertools as it
import os
from pathlib import Path

from aiida import orm
from aiida.common.log import AIIDA_LOGGER
from aiida.tools.dumping.base import BaseDumper
from aiida.tools.dumping.logger import DumpLogger
from aiida.tools.dumping.process import ProcessDumper

logger = AIIDA_LOGGER.getChild('tools.dumping')

class GroupDumper:
    def __init__(
        self,
        base_dumper: BaseDumper | None = None,
        process_dumper: ProcessDumper | None = None,
        dump_logger: DumpLogger | None = None,
        group: orm.Group | str | None = None,
        deduplicate: bool = True,
        output_path: Path | str | None = None,
    ):
        self.deduplicate = deduplicate

        # Allow passing of group via label
        if isinstance(group, str):
            group = orm.load_group(group)

        self.group = group

        self.base_dumper = base_dumper or BaseDumper()
        self.process_dumper = process_dumper or ProcessDumper()
        self.dump_logger = dump_logger or DumpLogger()

        # Properly set the `output_path` attribute

        self.output_path = Path(output_path or self.base_dumper.dump_parent_path)

        self.nodes = self._get_nodes()

    def _should_dump_processes(self) -> bool:
        return len([node for node in self.nodes if isinstance(node, orm.ProcessNode)]) > 0

    def _get_nodes(self):
        # Get all nodes that are in the group
        if self.group is not None:
            nodes = list(self.group.nodes)

        # Get all nodes that are _not_ in any group
        else:
            groups: list[orm.Group] = orm.QueryBuilder().append(orm.Group).all(flat=True)  # type: ignore[assignment]
            nodes_in_groups = [node.uuid for group in groups for node in group.nodes]

            # Need to expand here also with the called_descendants of `WorkflowNodes`, otherwise the called
            # `CalculationNode`s for `WorkflowNode`s that are part of a group are dumped twice
            # Get the called descendants of WorkflowNodes within the nodes_in_groups list
            called_descendants_generator = (
                orm.load_node(node).called_descendants
                for node in nodes_in_groups
                if isinstance(orm.load_node(node), orm.WorkflowNode)
            )

            # Flatten the list of called descendants
            sub_nodes_in_groups = list(it.chain(*called_descendants_generator))

            sub_nodes_in_groups = [node.uuid for node in sub_nodes_in_groups]
            nodes_in_groups += sub_nodes_in_groups

            profile_nodes = orm.QueryBuilder().append(orm.Node, project=['uuid']).all(flat=True)
            nodes = [profile_node for profile_node in profile_nodes if profile_node not in nodes_in_groups]
            nodes = [orm.load_node(node) for node in nodes]

        if self.base_dumper.last_dump_time is not None:
            nodes = [node for node in nodes if node.mtime > self.base_dumper.last_dump_time]

        return nodes

    def _get_processes(self):
        nodes = self.nodes
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

        calculations = set([node for node in nodes if isinstance(node, orm.CalculationNode)] + called_calculations)

        self.calculations = calculations
        self.workflows = workflows

    def _dump_processes(self):
        self._get_processes()

        if len(self.workflows) + len(self.calculations) == 0:
            logger.report('No workflows or calculations to dump in group.')
            return

        self._dump_calculations()
        self._dump_workflows()

    def _dump_calculations(self):
        calculations_path = self.output_path / 'calculations'
        dumped_calculations = {}

        for calculation in self.calculations:
            calculation_dumper = self.process_dumper

            calculation_dump_path = calculations_path / calculation_dumper._generate_default_dump_path(
                process_node=calculation, prefix=''
            )

            if calculation.caller is None:
                # or (calculation.caller is not None and not self.deduplicate):
                calculation_dumper._dump_calculation(calculation_node=calculation, output_path=calculation_dump_path)

                dumped_calculations[calculation.uuid] = calculation_dump_path

        self.dump_logger.update_calculations(dumped_calculations)

    def _dump_workflows(self):
        # workflow_nodes = get_nodes_from_db(aiida_node_type=orm.WorkflowNode, with_group=self.group, flat=True)
        workflow_path = self.output_path / 'workflows'
        workflow_path.mkdir(exist_ok=True, parents=True)
        dumped_workflows = {}

        for workflow in self.workflows:
            workflow_dumper = self.process_dumper

            workflow_dump_path = workflow_path / workflow_dumper._generate_default_dump_path(
                process_node=workflow, prefix=None
            )

            logged_workflows = self.dump_logger.get_logs()['workflows']

            if self.deduplicate and workflow.uuid in logged_workflows.keys():
                os.symlink(
                    src=logged_workflows[workflow.uuid],
                    dst=workflow_dump_path,
                )
            else:
                workflow_dumper._dump_workflow(
                    workflow_node=workflow,
                    output_path=workflow_dump_path,
                    # link_calculations=not self.deduplicate,
                    # link_calculations_dir=self.output_path / 'calculations',
                )

                dumped_workflows[workflow.uuid] = workflow_dump_path

        self.dump_logger.update_workflows(dumped_workflows)

    def dump(self):
        self.output_path.mkdir(exist_ok=True, parents=True)
        self._dump_processes()
