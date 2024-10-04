###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Functionality to dump AiiDA Groups."""

from __future__ import annotations

import contextlib
import itertools
import logging
import os
from pathlib import Path
from typing import List

from aiida import orm
from aiida.common import timezone
from aiida.tools.dumping.collection import CollectionDumper
from aiida.tools.dumping.data import DataDumper
from aiida.tools.dumping.process import ProcessDumper
from aiida.tools.dumping.utils import get_nodes_from_db, validate_make_dump_path
from collections import Counter
import os
from rich.pretty import pprint

logger = logging.getLogger(__name__)


class GroupDumper(CollectionDumper):
    def __init__(self, group: str | orm.Group, output_path: Path | str | None = None, **kwargs) -> None:
        super().__init__(**kwargs)
        if isinstance(group, str):
            group = orm.Group.get(self.group)
        self.group = group
        self.hidden_aiida_path = self.parent_path / '.aiida-raw-data'

        # if group_name.startswith('pseudo'):
        group_subdir = Path(*self.group.type_string.split('.'))

        if output_path is None:
            try:
                output_path = self.parent_path / 'groups' / group_subdir / self.group.label
            except:
                raise ValueError('Error setting up `output_path`. Must be set manually.')
        else:
            # TODO: Add validation here
            output_path.mkdir(exist_ok=True, parents=True)
        self.output_path = output_path

        if not hasattr(self, 'entity_counter'):
            self.create_entity_counter()

    def create_entity_counter(self):
        # If the group only has one WorkChain assigned to it, this will only return a count of 1 for the
        # WorkChainNode, nothing more, that is, not recursively.
        entity_counter = Counter()

        # Iterate over all the entities in the group
        for entity in self.group.nodes:
            # Count the type string of each entity
            entity_counter[entity.__class__] += 1

        # Convert the Counter to a dictionary (optional)
        self.entity_counter = entity_counter
        return entity_counter

    def dump_processes(self):
        # ? Here, these could be all kinds of entities that could be grouped in AiiDA
        # if output_path is None:
        #     output_path = Path.cwd()

        self.last_dumped = timezone.now()

        workflows = [node for node in self.group.nodes if isinstance(node, orm.WorkflowNode)]

        # Also need to obtain sub-calculations that were called by workflows of the group
        # These are not contained in the group.nodes directly
        called_calculations = []
        for workflow in workflows:
            called_calculations += [
                node for node in workflow.called_descendants if isinstance(node, orm.CalculationNode)
            ]

        calculations = set(
            [node for node in self.group.nodes if isinstance(node, orm.CalculationNode)] + called_calculations
        )

        if self.calculations_hidden:
            self._dump_calculations_hidden(calculations=calculations)
            self._dump_link_workflows(workflows=workflows)
            self._link_calculations_hidden(calculations=calculations)
        else:
            for workflow in workflows:
                process_dumper = ProcessDumper(**self.kwargs)
                workflow_path = process_dumper._generate_default_dump_path(process_node=workflow)
                process_dumper.dump(process_node=workflow, output_path=workflow_path)

    def dump_core_data(self):
        if self.data_hidden:
            data = [node for node in self.group.nodes if isinstance(node, (orm.Data, orm.Computer))]
            self._dump_data_hidden(data_nodes=data)
        else:
            # TODO: Add functionality of ProcessDumper to also dump the associated data nodes directly
            pass

    def dump_plugin_data(self):
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
