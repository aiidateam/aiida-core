###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Functionality for dumping of profile data."""

from __future__ import annotations

import contextlib
import logging
import sys
from pathlib import Path
from typing import List

import yaml

from aiida import orm
from aiida.manage.configuration.profile import Profile
from aiida.orm import CalculationNode, Code, Computer, Group, QueryBuilder, StructureData, User, WorkflowNode
from aiida.orm.groups import ImportGroup
from collections import Counter

from aiida.tools.dumping.collection import CollectionDumper
from aiida.tools.dumping.group import GroupDumper
from aiida.tools.dumping.process import ProcessDumper
from aiida.tools.dumping.data import DataDumper

from aiida.tools.dumping.utils import validate_make_dump_path, get_nodes_from_db
from aiida.common import timezone
from rich.pretty import pprint

logger = logging.getLogger(__name__)
DEFAULT_ENTITIES_TO_DUMP = [WorkflowNode, StructureData, User, Code, Computer]
DEFAULT_COLLECTIONS_TO_DUMP = [Group]  # ? Might not be needed -> Main useful collection type is just Group
PROFILE_DUMP_JSON_FILE = 'profile-dump-info.json'
DEFAULT_PROCESSES_TO_DUMP = [orm.CalculationNode, orm.WorkflowNode]  # , StructureData, User, Code, Computer]
DEFAULT_DATA_TO_DUMP = [orm.StructureData, orm.Code, orm.Computer, ]  # , StructureData, User, Code, Computer]
DEFAULT_ENTITIES_TO_DUMP = DEFAULT_PROCESSES_TO_DUMP + DEFAULT_DATA_TO_DUMP


class ProfileDumper(CollectionDumper):
    def __init__(
        self,
        # profile: str,
        # parent_path: str | Path = Path(),
        # full: bool = False,
        entities_to_dump: List | None = None,
        organize_by_groups: bool = True,
        process_dumper_kwargs: dict | None = None,
        config: Path | dict | None = None,
        **kwargs
    ):
        super().__init__(**kwargs)
        self.kwargs = kwargs

        self.config = config

        if entities_to_dump is not None:
            self.entities_to_dump = entities_to_dump
        else:
            self.entities_to_dump = DEFAULT_ENTITIES_TO_DUMP

        if process_dumper_kwargs is None:
            process_dumper_kwargs = {}
        self.process_dumper_kwargs = process_dumper_kwargs

        # self.entity_counter_dictionary = dict.fromkeys(self.entities_to_dump, 0)
        self.entity_counter_dictionary = {cls.__name__: 0 for cls in self.entities_to_dump}

        self.profile_dump_json_file = self.parent_path / PROFILE_DUMP_JSON_FILE

    def _create_entity_counter(self):
        nodes = orm.QueryBuilder().append(orm.Node).all(flat=True)
        entity_counter = Counter()

        for entity in nodes:
            entity_counter[entity.__class__] += 1

        self.entity_counter = entity_counter
        return entity_counter

    def update_info_file(self):
        import json
        import os
        from datetime import datetime

        from aiida.manage.configuration import get_config

        # Get the current timestamp
        now = datetime.now()
        new_entry = {'timestamp': now.strftime('%Y-%m-%d %H:%M:%S')}

        # Get the profile configuration
        config = get_config()
        profile_info = config.dictionary  # Assuming this is a dictionary

        run_key = 'last_run_time'
        profile_key = 'latest_profile_info'

        # Read the existing data from the JSON file if it exists
        if os.path.exists(self.profile_dump_json_file):
            with open(self.profile_dump_json_file, 'r') as json_file:
                try:
                    data = json.load(json_file)
                except json.JSONDecodeError:
                    data = {run_key: [], profile_key: {}}
        else:
            data = {run_key: [], profile_key: {}}

        # Append the new entry to the existing data
        data[run_key].append(new_entry)

        # Update the profile info with the latest one
        data[profile_key] = profile_info

        # Write the updated data back to the JSON file
        with open(self.profile_dump_json_file, 'w') as json_file:
            json.dump(data, json_file, indent=4)

    def dump_processes(self, output_path: Path | str | None = None):
        # ? Here, these could be all kinds of entities that could be grouped in AiiDA
        # if output_path is None:
        #     output_path = Path.cwd()

        self.last_dumped = timezone.now()
        nodes = orm.QueryBuilder().append(orm.Node).all(flat=True)

        # TODO: Add validation here
        if output_path is None:
            output_path = self.parent_path

        output_path.mkdir(exist_ok=True, parents=True)

        if not hasattr(self, 'entity_counter'):
            self.create_entity_counter()
        # pprint(self.entity_counter)

        # ? This here now really relates to each individual group
        self.output_path = output_path

        workflows = [node for node in nodes if isinstance(node, orm.WorkflowNode)]

        # Also need to obtain sub-calculations that were called by workflows of the group
        # These are not contained in the group.nodes directly
        called_calculations = []
        for workflow in workflows:
            called_calculations += [
                node for node in workflow.called_descendants if isinstance(node, orm.CalculationNode)
            ]

        calculations = set(
            [node for node in nodes if isinstance(node, orm.CalculationNode)] + called_calculations
        )

        self._dump_calculations_hidden(calculations=calculations)
        self._dump_link_workflows(workflows=workflows)
        self._link_calculations_hidden(calculations=calculations)

    def dump_core_data(self):
        nodes = orm.QueryBuilder().append(orm.Node).all(flat=True)
        data = [node for node in nodes if isinstance(node, (orm.Data, orm.Computer))]
        if self.data_hidden:
            self._dump_data_hidden(data_nodes=data)
        else:
            pass

    def dump_plugin_data(self):
        from importlib.metadata import entry_points

        plugin_data_entry_points = entry_points(group='aiida.data')
        print(plugin_data_entry_points)
