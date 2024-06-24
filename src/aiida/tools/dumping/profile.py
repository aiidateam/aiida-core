# Maybe abstract this, as one might not only want to dump an archive, but also a group, or other collections of nodes?
# Generally work with uuids, not Node instances, until the node instance is actually required, for performance reasons
# Need skip-existing option, either for the AbstractDumper, or the dumpers in general
#
# ? Possibly make first get_entity functions and then dump functions; or _get_entity functions that are called by the
# dumping
# ? Could implement incremental dumping via try-except on FileExistsError, or write the list of hashes of the dumped
# entities to disk, and then read that in for each dumping call
# ? Check for self.full inside each dumping function or once in a `full_rewrite` function?
# ? How to handle nested workchains
# ? Add some extras configuration to the directory naming?
# ❯ verdi node extras 41
# PK: 41
# {
#     "configuration": "X/Diamond",
#     "element": "Ta"
# }
# ? How to handle `ImportGroup`s?
# ? Implement `dry_run` option
# ? Should add a function to dump only CalcJob?
# ? Use normal logger or AiiDA_LOGGER?
# ? Add clean_before option in addition to "full"?
# ? Automatically remove "structure" or "workflows" from path, if group name contains that? -> Don't think this is a
# good idea
# ? Abstract `dump_structure_data` and `dump_workflows` so that I can iterate over them based on the entities_to_dump
# ? Dump codes and computers YAML files
# ? Also dump user-info

from __future__ import annotations

import logging
from pathlib import Path
from typing import List

from aiida.orm import Group, QueryBuilder, StructureData, WorkflowNode, CalculationNode, Code, Computer, User
from aiida.orm.groups import ImportGroup
from aiida.tools.dumping.processes import ProcessDumper
from pprint import pprint
import sys


LOGGER = logging.getLogger(__name__)


class ProfileDumper:
    def __init__(
        self,
        profile: str,
        parent_path: str | Path = Path(),
        full: bool = False,
        entities_to_dump: List | None = None,
        organize_by_groups: bool = True,
        dry_run: bool = False,
        process_dumper_kwargs: dict | None = None,
    ):
        self.profile = profile
        self.parent_path = Path(parent_path)
        self.full = full
        self.organize_by_groups = organize_by_groups
        self.dry_run = dry_run

        # ? These here relate to sorting by groups
        self.group_sub_path = Path()
        self.current_group = None

        if self.organize_by_groups:
            profile_groups = QueryBuilder().append(Group).all(flat=True)
            profile_groups = [group for group in profile_groups if not isinstance(group, ImportGroup)]
            self.profile_groups = profile_groups

        if entities_to_dump is not None:
            self.entities_to_dump = entities_to_dump
        else:
            self.entities_to_dump = [StructureData, WorkflowNode]

        if full:
            LOGGER.report('Full set to True. Will overwrite previous directories.')

        if process_dumper_kwargs is None:
            process_dumper_kwargs = {}
        self.process_dumper_kwargs = process_dumper_kwargs

    @staticmethod
    def check_storage_size_user():
        from aiida.manage.manager import get_manager

        manager = get_manager()
        storage = manager.get_profile_storage()

        data = storage.get_info(detailed=True)
        repository_data = data['repository']['Size (MB)']
        total_size_gb = sum(repository_data.values()) / 1024
        if total_size_gb > 10:
            user_input = (
                input('Repository size larger than 10gb. Do you still want to dump the profile data? (y/N): ')
                .strip()
                .lower()
            )

            if user_input != 'y':
                sys.exit()

    @staticmethod
    def get_nodes_from_db(aiida_node_type, with_group: str | None = None):
        qb = QueryBuilder()

        if with_group:
            qb.append(Group, filters={'label': with_group.label}, tag='with_group')
            qb.append(aiida_node_type, with_group='with_group')
        else:
            qb.append(aiida_node_type)

        num_nodes = qb.count()
        return qb.iterall() if num_nodes > 10 ^ 3 else qb.all()

    @staticmethod
    def update_info_file(file_path):
        import json
        import os
        from datetime import datetime

        # Get the current timestamp
        now = datetime.now()
        new_entry = now.strftime('%Y-%m-%d %H:%M:%S')
        run_key = 'last_run_time'

        # Read the existing data from the JSON file if it exists
        if os.path.exists(file_path):
            with open(file_path, 'r') as json_file:
                try:
                    data = json.load(json_file)
                except json.JSONDecodeError:
                    data = {run_key: []}
        else:
            data = {run_key: []}

        # Append the new entry to the existing data
        data[run_key].append(new_entry)

        # Write the updated data back to the JSON file
        with open(file_path, 'w') as json_file:
            json.dump(data, json_file, indent=4)

    def dump(self):
        if self.organize_by_groups:
            LOGGER.report('Dumping sorted by groups.')
            for group in self.profile_groups:
                LOGGER.report(f'Dumping group: {group}')
                self.current_group = group
                self.group_sub_path = self.parent_path / 'groups' / Path(self.current_group.label)
                self.resolve_dump_entities()
        else:
            self.resolve_dump_entities()

        self.update_info_file(file_path=self.parent_path / 'profile-dump-info.json')

    def resolve_dump_entities(self):
        if WorkflowNode in self.entities_to_dump:
            self.dump_workflows()
        if StructureData in self.entities_to_dump:
            self.dump_structures()
        if CalculationNode in self.entities_to_dump:
            self.dump_calculations()
        if Code in self.entities_to_dump or Computer in self.entities_to_dump:
            self.dump_code_computers()
        if User in self.entities_to_dump:
            self.dump_user_info()

    def dump_structures(self, format: str = 'cif'):
        structure_datas = self.get_nodes_from_db(aiida_node_type=StructureData, with_group=self.current_group)

        for structure_data_ in structure_datas:
            # QB returns list...
            structure_data = structure_data_[0]
            structures_path = Path(self.parent_path / self.group_sub_path / 'structures')

            structures_path.mkdir(exist_ok=True, parents=True)

            structure_name = f'{structure_data.get_formula()}-{structure_data.pk}.{format}'

            if self.full:
                structure_data.export(path=structures_path / structure_name, fileformat=format, overwrite=True)
            else:
                try:
                    structure_data.export(path=structures_path / structure_name, fileformat=format, overwrite=False)
                except OSError:
                    continue

    def dump_workflows(self, only_parents: bool = True):
        # ? Dump only top-level workchains, as that includes sub-workchains already

        if self.organize_by_groups:
            workflows = self.get_nodes_from_db(aiida_node_type=WorkflowNode, with_group=self.current_group)
        else:
            workflows = self.get_nodes_from_db(aiida_node_type=WorkflowNode)

        for iworkflow_, workflow_ in enumerate(workflows):
            workflow = workflow_[0]

            if only_parents and workflow.caller is not None:
                continue

            workflow_dumper = ProcessDumper(**self.process_dumper_kwargs, overwrite=self.full)

            workflow_dump_path = (
                self.parent_path
                / self.group_sub_path
                / 'workflows'
                / ProcessDumper._generate_default_dump_path(process_node=workflow)
            )

            try:
                workflow_dumper.dump(process_node=workflow, output_path=workflow_dump_path)
            except FileExistsError:
                pass

            # To make development quicker
            if iworkflow_ > 1:
                break

    # Scaffolding

    @classmethod
    def read_user_config(cls):
        pass

    def dump_code_computers(self):
        pass

    def dump_user_info(self):
        pass

    def node_exists_on_disk(self):
        pass

    def dump_calculations(self):
        pass
