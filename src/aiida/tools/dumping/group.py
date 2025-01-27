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
from collections import defaultdict
import itertools as it
import logging
from pathlib import Path

from aiida import orm
from aiida.tools.dumping.base import BaseDumper
from aiida.tools.dumping.process import ProcessDumper

logger = logging.getLogger(__name__)

DEFAULT_PROCESSES_TO_DUMP = [orm.CalculationNode, orm.WorkflowNode]
# DEFAULT_DATA_TO_DUMP = [orm.StructureData, orm.Code, orm.Computer, orm.BandsData, orm.UpfData]
# DEFAULT_COLLECTIONS_TO_DUMP ??
DEFAULT_ENTITIES_TO_DUMP = DEFAULT_PROCESSES_TO_DUMP  # + DEFAULT_DATA_TO_DUMP


class GroupDumper:
    def __init__(
        self,
        base_dumper: BaseDumper | None = None,
        process_dumper: ProcessDumper | None = None,
        group: orm.Group | str | None = None,
        deduplicate: bool = True,
        output_path: str | Path | None = None,
        global_log_dict: dict[str, Path] | None = None
    ):
        self.deduplicate = deduplicate

        # Allow passing of group via label
        if isinstance(group, str):
            group = orm.Group.get(group)

        self.group = group
        self.output_path = output_path
        self.global_log_dict = global_log_dict

        if base_dumper is None:
            base_dumper = BaseDumper()
        self.base_dumper: BaseDumper = base_dumper

        if process_dumper is None:
            process_dumper = ProcessDumper()
        self.process_dumper: ProcessDumper = process_dumper

        self.nodes = self._get_nodes()
        self.log_dict = {}

    def _should_dump_processes(self) -> bool:

        return len([node for node in self.nodes if isinstance(node, orm.ProcessNode)]) > 0

    def _get_nodes(self):

        # Get all nodes that are in the group
        if self.group is not None:
            nodes = list(self.group.nodes)

        # Get all nodes that are _not_ in any group
        else:
            groups = orm.QueryBuilder().append(orm.Group).all(flat=True)
            nodes_in_groups = [node.uuid for group in groups for node in group.nodes]
            # Need to expand here also with the called_descendants of `WorkflowNodes`, otherwise the called
            # `CalculationNode`s for `WorkflowNode`s that are part of a group are dumped twice
            sub_nodes_in_groups = list(
                it.chain(
                    *[
                        orm.load_node(node).called_descendants
                        for node in nodes_in_groups
                        if isinstance(orm.load_node(node), orm.WorkflowNode)
                    ]
                )
            )
            sub_nodes_in_groups = [node.uuid for node in sub_nodes_in_groups]
            nodes_in_groups = nodes_in_groups + sub_nodes_in_groups

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

        self.log_dict = {
            'calculations': {},
            # dict.fromkeys([c.uuid for c in self.calculations], None),
            'workflows': dict.fromkeys([w.uuid for w in workflows], None)
        }

    def _dump_processes(self):

        self._get_processes()

        if len(self.workflows) + len(self.calculations) == 0:
            logger.report("No workflows or calculations to dump in group.")
            return

        self.output_path.mkdir(exist_ok=True, parents=True)

        self._dump_calculations()
        self._dump_workflows()

    def _dump_calculations(self):

        calculations_path = self.output_path / 'calculations'

        for calculation in self.calculations:
            calculation_dumper = self.process_dumper

            calculation_dump_path = (
                calculations_path / calculation_dumper._generate_default_dump_path(process_node=calculation, prefix='')
            )

            if calculation.caller is None:
                # or (calculation.caller is not None and not self.deduplicate):
                calculation_dumper._dump_calculation(calculation_node=calculation, output_path=calculation_dump_path)

                self.log_dict['calculations'][calculation.uuid] = calculation_dump_path

    def _dump_workflows(self):
        # workflow_nodes = get_nodes_from_db(aiida_node_type=orm.WorkflowNode, with_group=self.group, flat=True)
        workflow_path = self.output_path / 'workflows'
        workflow_path.mkdir(exist_ok=True, parents=True)

        for workflow in self.workflows:

            workflow_dumper = self.process_dumper

            workflow_dump_path = (
                workflow_path / workflow_dumper._generate_default_dump_path(process_node=workflow, prefix=None)
            )

            if self.deduplicate and workflow.uuid in self.global_log_dict["workflows"].keys():
                os.symlink(
                    src=self.global_log_dict["workflows"][workflow.uuid],
                    dst=workflow_dump_path,
                )
            else:
                workflow_dumper._dump_workflow(
                    workflow_node=workflow,
                    output_path=workflow_dump_path,
                    # link_calculations=not self.deduplicate,
                    # link_calculations_dir=self.output_path / 'calculations',
                )

                self.log_dict['workflows'][workflow.uuid] = workflow_dump_path
