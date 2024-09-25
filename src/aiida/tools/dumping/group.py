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
    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)

    def create_entity_counter(self, group: orm.Group | str):
        # ? If the group only has one WorkChain assigned to it, this will only return a count of 1 for the
        # ? WorkChainNode, nothing more, that is, not recursively.
        if isinstance(group, str):
            group = orm.Group.get(group)
            self.group = group
        entity_counter = Counter()

        # Iterate over all the entities in the group
        for entity in group.nodes:
            # Count the type string of each entity
            entity_counter[entity.__class__] += 1

        # Convert the Counter to a dictionary (optional)
        self.entity_counter = entity_counter
        return entity_counter

    def dump(self, group: orm.Group | str | None = None, output_path: Path | str | None = None):
        # ? Here, these could be all kinds of entities that could be grouped in AiiDA
        # if output_path is None:
        #     output_path = Path.cwd()

        self.last_dumped = timezone.now()
        self.group = group

        if group is None:
            raise Exception('Group must be set')

        self.group_name = group.label if isinstance(group, orm.Group) else group

        if output_path is None:
            try:
                output_path = self.parent_path / 'groups' / self.group_name
            except:
                raise ValueError('Error setting up `output_path`. Must be set manually.')
        else:
            # TODO: Add validation here
            output_path.mkdir(exist_ok=True, parents=True)

        self.create_entity_counter(group=group)
        pprint(self.entity_counter)

        self.hidden_aiida_path = self.parent_path / '.aiida-raw-data'

        # ? This here now really relates to each individual group
        self.output_path = output_path
        # self.group_path = Path.cwd() / 'groups'
        # self.group_path = self.output_path / 'groups' / group_name

        # logger.report(f'self.entity_counter for Group <{self.group}>: {self.entity_counter}')
        # logger.report(f'Dumping calculations and workflows of group {group_name}...')

        # TODO: This shouldn't be on a per-group basis? Possibly dump all data for the whole profile.
        # TODO: Though, now that I think about it, it might actually be desirable to only limit that to the group only.
        # logger.report(f'Dumping raw calculation data for group {group_name}...')

        if self.dump_processes:
            # if self.should_dump_calculations() or self.should_dump_workflows():
            logger.report(f'Dumping calculations for group {self.group_name}...')

            # def _obtain_workflows(): ...
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

            self._dump_calculations_hidden(calculations=calculations)
            self._dump_link_workflows(workflows=workflows)
            self._link_calculations_hidden(calculations=calculations)

        if self.dump_data:
            logger.report(f'Dumping data for group {self.group_name}...')
            # data = [node for node in self.group.nodes if isinstance(node, orm.Data)]
            data = [node for node in self.group.nodes if isinstance(node, orm.StructureData)]
            print('DATA', data)
            self._dump_data_hidden(data_nodes=data)

