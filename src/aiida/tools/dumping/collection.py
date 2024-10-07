###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Functionality for dumping of a Collections of AiiDA ORMs."""

from __future__ import annotations

import contextlib
import logging
import os
from collections import Counter
from pathlib import Path
from typing import List

from aiida import orm
from aiida.tools.dumping.data import DataDumper
from aiida.tools.dumping.processes import ProcessDumper
from aiida.tools.dumping.rich import DEFAULT_CORE_EXPORT_MAPPING
from aiida.tools.dumping.utils import sanitize_file_extension

logger = logging.getLogger(__name__)

DEFAULT_PROCESSES_TO_DUMP = [orm.CalculationNode, orm.WorkflowNode]
DEFAULT_DATA_TO_DUMP = [orm.StructureData, orm.Code, orm.Computer, orm.BandsData, orm.UpfData]
# DEFAULT_COLLECTIONS_TO_DUMP ??
DEFAULT_ENTITIES_TO_DUMP = DEFAULT_PROCESSES_TO_DUMP + DEFAULT_DATA_TO_DUMP


# ! This class is instantiated once for every group, or once for the full profile
class CollectionDumper:
    def __init__(
        self,
        *args,
        dump_parent_path: Path = Path().cwd(),
        output_path: Path = Path().cwd(),
        overwrite: bool = False,
        should_dump_processes: bool = False,
        should_dump_data: bool = False,
        calculations_hidden: bool = False,
        data_hidden: bool = False,
        no_organize_by_groups: bool = False,
        entities_to_dump: set = {},
        group: orm.Group | None = None,
        process_dumper: ProcessDumper | None = None,
        data_dumper: DataDumper | None = None,
        **kwargs,
    ):
        self.args = args
        self.dump_parent_path = dump_parent_path
        self.output_path = output_path
        self.overwrite = overwrite
        self.should_dump_processes = should_dump_processes
        self.should_dump_data = should_dump_data
        self.calculations_hidden = calculations_hidden
        self.data_hidden = data_hidden
        self.no_organize_by_groups = no_organize_by_groups
        self.entities_to_dump = entities_to_dump
        self.process_dumper = process_dumper
        self.data_dumper = data_dumper
        self.kwargs = kwargs

        self.hidden_aiida_path = dump_parent_path / '.aiida-raw-data'

        # Allow passing of group via label
        if isinstance(group, str):
            group = orm.Group.get(self.group)
        self.group = group

        self.output_path = output_path
        self.output_path.mkdir(exist_ok=True, parents=True)

        if not hasattr(self, 'entity_counter'):
            self.create_entity_counter()

    def create_entity_counter(self) -> Counter:
        # If the group only has one WorkChain assigned to it, this will only return a count of 1 for the
        # WorkChainNode, nothing more, that is, not recursively.
        entity_counter = Counter()
        if self.group is not None:
            nodes = self.group.nodes
        else:
            nodes = orm.QueryBuilder().append(orm.Node).all(flat=True)

        # Iterate over all the entities in the group
        for node in nodes:
            # Count the type string of each entity
            entity_counter[node.__class__] += 1

        # Convert the Counter to a dictionary (optional)
        self.entity_counter = entity_counter

        return entity_counter

    def _should_dump_processes(self) -> bool:
        return (
            sum(
                self.entity_counter.get(orm_process_class, 0)
                for orm_process_class in [
                    orm.CalcJobNode,
                    orm.CalcFunctionNode,
                    orm.WorkChainNode,
                    orm.WorkFunctionNode,
                    orm.ProcessNode,
                ]
            )
            > 0
        )

    def _dump_calculations_hidden(self, calculations):
        # ? Dump only top-level workchains, as that includes sub-workchains already

        for calculation in calculations:
            calculation_dumper = self.process_dumper

            calculation_dump_path = self.hidden_aiida_path / 'calculations' / calculation.uuid

            # if not self.dry_run:
            # with contextlib.suppress(FileExistsError):
            try:
                calculation_dumper._dump_calculation(calculation_node=calculation, output_path=calculation_dump_path)
            except:
                raise

            # # To make development quicker
            # if iworkflow_ > 1:
            #     break

    def _dump_link_workflows(self, workflows, link_calculations: bool = True):
        # workflow_nodes = get_nodes_from_db(aiida_node_type=orm.WorkflowNode, with_group=self.group, flat=True)
        for workflow in workflows:
            workflow_dumper = self.process_dumper

            link_calculations_dir = self.hidden_aiida_path / 'calculations'
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
                link_calculations=link_calculations,
                link_calculations_dir=link_calculations_dir,
            )

    def _link_calculations_hidden(self, calculations):
        # calculation_nodes = get_nodes_from_db(aiida_node_type=orm.CalculationNode, with_group=self.group, flat=True)
        for calculation_node in calculations:
            calculation_dumper = self.process_dumper

            link_calculations_dir = self.hidden_aiida_path / 'calculations'
            # link_calculations_dir.mkdir(parents=True, exist_ok=True)

            calculation_dump_path = self.output_path / 'calculations'
            calculation_dump_path.mkdir(parents=True, exist_ok=True)
            calculation_dump_path = calculation_dump_path / calculation_dumper._generate_default_dump_path(
                process_node=calculation_node
            )

            with contextlib.suppress(FileExistsError):
                os.symlink(link_calculations_dir / calculation_node.uuid, calculation_dump_path)

    def get_collection_nodes(self):
        if hasattr(self, 'collection_nodes'):
            return self.collection_nodes

        # Get all nodes that are in the group
        if self.group is not None:
            nodes = self.group.nodes

        # Get all nodes that are _not_ in any group
        else:
            groups = orm.QueryBuilder().append(orm.Group).all(flat=True)
            nodes_in_groups = [node.pk for group in groups for node in group.nodes]
            profile_nodes = orm.QueryBuilder().append(orm.Node, project=['pk']).all(flat=True)
            nodes = [profile_node for profile_node in profile_nodes if profile_node not in nodes_in_groups]
            nodes = [orm.load_node(node) for node in nodes]

        self.collection_nodes = nodes

        return nodes

    def dump_processes(self):
        # ? Here, these could be all kinds of entities that could be grouped in AiiDA
        # if len(self.entities_to_dump) > 0:
        #     pass
        #     # nodes = self.entities_to_dump
        # else:
        nodes = self.get_collection_nodes()
        workflows = [node for node in nodes if isinstance(node, orm.WorkflowNode)]

        # Also need to obtain sub-calculations that were called by workflows of the group
        # These are not contained in the group.nodes directly
        called_calculations = []
        for workflow in workflows:
            called_calculations += [
                node for node in workflow.called_descendants if isinstance(node, orm.CalculationNode)
            ]

        calculations = set([node for node in nodes if isinstance(node, orm.CalculationNode)] + called_calculations)

        if self.calculations_hidden:
            self._dump_calculations_hidden(calculations=calculations)
            self._dump_link_workflows(workflows=workflows)
            self._link_calculations_hidden(calculations=calculations)
        else:
            for workflow in workflows:
                workflow_path = (
                    self.output_path
                    / 'workflows'
                    / self.process_dumper._generate_default_dump_path(process_node=workflow)
                )
                self.process_dumper.dump(process_node=workflow, output_path=workflow_path)

    def dump_core_data_rich(self):

        nodes = self.get_collection_nodes()
        nodes = [node for node in nodes if isinstance(node, (orm.Data, orm.Computer))]
        nodes = [node for node in nodes if node.entry_point.name.startswith('core')]
        data_dumper = self.data_dumper

        for data_node in nodes:
            node_entry_point_name = data_node.entry_point.name

            # Get the file format for the data node
            fileformat = data_dumper.rich_options_dict[node_entry_point_name]['export_format']
            # Don't go further if no importer implemented for a data type anyway
            exporter = data_dumper.rich_options_dict[node_entry_point_name]['exporter']
            print(f'data_node: {data_node}, fileformat: {fileformat}, exporter: {exporter}')
            if exporter is None:
                continue

            try:
                # Generate a nice filename and sanitize it
                nice_output_path = self.output_path / 'data' / data_node.__class__.__name__.lower()
                nice_fname = data_dumper.generate_output_fname_rich(data_node=data_node, fileformat=fileformat).replace(
                    '__', '_'
                )
                nice_fname = sanitize_file_extension(nice_fname)

                if data_dumper.data_hidden:
                    # Define paths for hidden dump and linking
                    hidden_dump_path = self.hidden_aiida_path / 'data' / data_node.__class__.__name__.lower()
                    uuid_fname = sanitize_file_extension(f'{data_node.uuid}.{fileformat}')

                    # Dump the data in the hidden directory
                    data_dumper.dump_rich_core(data_node, hidden_dump_path, uuid_fname)

                    # Link the hidden file to the expected output path
                    (nice_output_path / nice_fname).parent.mkdir(exist_ok=True, parents=True)
                    os.symlink(hidden_dump_path / uuid_fname, nice_output_path / nice_fname)

                else:
                    # Dump the data in the non-hidden directory
                    data_dumper.dump_rich_core(data_node, nice_output_path, nice_fname)

            except TypeError:
                # Handle case when no exporter is implemented for a given data_node type
                pass
            except Exception:
                raise

    def dump_plugin_data(self):
        return
        from importlib.metadata import entry_points

        plugin_data_entry_points = [entry_point.name for entry_point in entry_points(group='aiida.data')]
        # print(plugin_data_entry_points)
        # print(self.entity_counter)
        from aiida.manage.manager import get_manager

        manager = get_manager()
        storage = manager.get_profile_storage()
        orm_entities = storage.get_orm_entities(detailed=True)['Nodes']['node_types']
        non_core_data_entities = [
            orm_entity
            for orm_entity in orm_entities
            if orm_entity.startswith('data') and not orm_entity.startswith('data.core')
        ]
        # TODO: Implement dumping here. Stashed for now, as both `HubbardStructureData` and `UpfData` I wanted to use
        # TODO: for testing don't implement `export` either way
        # print(non_core_data_entities)
