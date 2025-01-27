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
import logging
from collections import Counter
from pathlib import Path

from aiida import orm
from aiida.tools.dumping.base import BaseDumper
from aiida.tools.dumping.process import ProcessDumper

logger = logging.getLogger(__name__)

DEFAULT_PROCESSES_TO_DUMP = [orm.CalculationNode, orm.WorkflowNode]
# DEFAULT_DATA_TO_DUMP = [orm.StructureData, orm.Code, orm.Computer, orm.BandsData, orm.UpfData]
# DEFAULT_COLLECTIONS_TO_DUMP ??
DEFAULT_ENTITIES_TO_DUMP = DEFAULT_PROCESSES_TO_DUMP  # + DEFAULT_DATA_TO_DUMP


# ! This class is instantiated once for every group, or once for the full profile
class GroupDumper:
    def __init__(
        self,
        base_dumper: BaseDumper | None = None,
        process_dumper: ProcessDumper | None = None,
        group: orm.Group | str | None = None,
        deduplicate: bool = True,
        output_path: str | Path | None = None,
    ):
        self.deduplicate = deduplicate

        # Allow passing of group via label
        if isinstance(group, str):
            group = orm.Group.get(group)

        self.group = group
        self.output_path = output_path

        if base_dumper is None:
            base_dumper = BaseDumper()
        self.base_dumper: BaseDumper = base_dumper

        if process_dumper is None:
            process_dumper = ProcessDumper()
        self.process_dumper: ProcessDumper = process_dumper

        if not hasattr(self, 'entity_counter'):
            self.create_entity_counter()

    def create_entity_counter(self) -> Counter:
        entity_counter = Counter()
        if self.group is not None:
            # If the group only has one WorkChain assigned to it, this will only return a count of 1 for the
            # WorkChainNode, nothing more, that is, it doesn't work recursively.
            nodes = self.group.nodes
        # elif self.nodes is not None:
        #     nodes = self.nodes
        else:
            nodes = orm.QueryBuilder().append(orm.Node).all(flat=True)

        # Iterate over all the entities in the group
        for node in nodes:
            # Count the type string of each entity
            entity_counter[node.__class__] += 1

        # Convert the Counter to a dictionary (optional)
        self.entity_counter = entity_counter

        return entity_counter

    def get_group_nodes(self):
        # if self.nodes:
        #     self.collection_nodes = self.nodes

        # if hasattr(self, 'collection_nodes'):
        #     return self.collection_nodes

        # Get all nodes that are in the group
        if self.group is not None:
            nodes = list(self.group.nodes)

        # Get all nodes that are _not_ in any group
        else:
            groups = orm.QueryBuilder().append(orm.Group).all(flat=True)
            nodes_in_groups = [node.pk for group in groups for node in group.nodes]
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
            sub_nodes_in_groups = [node.pk for node in sub_nodes_in_groups]
            nodes_in_groups = nodes_in_groups + sub_nodes_in_groups

            profile_nodes = orm.QueryBuilder().append(orm.Node, project=['pk']).all(flat=True)
            nodes = [profile_node for profile_node in profile_nodes if profile_node not in nodes_in_groups]
            nodes = [orm.load_node(node) for node in nodes]

        if self.base_dumper.last_dump_time is not None:
            # breakpoint()
            nodes = [node for node in nodes if node.mtime > self.base_dumper.last_dump_time]

        self.collection_nodes = nodes

        return nodes

    def _should_dump_processes(self) -> bool:
        if not hasattr(self, 'group_nodes'):
            self.get_group_nodes()

        return len([node for node in self.collection_nodes if isinstance(node, orm.ProcessNode)]) > 0

    def _dump_calculations(self, calculations):
        for calculation in calculations:
            calculation_dumper = self.process_dumper

            calculation_dump_path = (
                self.output_path
                / 'calculations'
                / calculation_dumper._generate_default_dump_path(process_node=calculation, prefix='')
            )

            if calculation.caller is None or (calculation.caller is not None and self.deduplicate):
                calculation_dumper._dump_calculation(calculation_node=calculation, output_path=calculation_dump_path)

    def _dump_workflows(self, workflows):
        # workflow_nodes = get_nodes_from_db(aiida_node_type=orm.WorkflowNode, with_group=self.group, flat=True)
        for workflow in workflows:
            # if workflow.pk == 47:
            #     breakpoint()

            workflow_dumper = self.process_dumper

            # TODO: If the GroupDumper is called from somewhere else outside, prefix the path with `groups/core` etc
            workflow_dump_path = (
                self.output_path
                / 'workflows'
                / workflow_dumper._generate_default_dump_path(process_node=workflow, prefix=None)
            )
            # logger.report(f'WORKFLOW_DUMP_PATH: {workflow_dump_path}')
            workflow_dumper._dump_workflow(
                workflow_node=workflow,
                output_path=workflow_dump_path,
                link_calculations=self.deduplicate,
                link_calculations_dir=self.output_path / 'calculations',
            )

    def _dump_processes(self):
        nodes = self.get_group_nodes()
        workflows = [node for node in nodes if isinstance(node, orm.WorkflowNode)]

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

        if len(workflows) + len(calculations) == 0:
            return

        self.output_path.mkdir(exist_ok=True, parents=True)

        self._dump_calculations(calculations=calculations)
        self._dump_workflows(workflows=workflows)
