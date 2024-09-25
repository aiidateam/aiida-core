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

from aiida.tools.dumping.collection import CollectionDumper
from aiida.tools.dumping.group import GroupDumper
from aiida.tools.dumping.process import ProcessDumper
from aiida.tools.dumping.data import DataDumper

from aiida.tools.dumping.utils import _validate_make_dump_path, get_nodes_from_db

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

        # self.profile = profile
        # self.parent_path = Path(parent_path)
        # self.full = full
        self.organize_by_groups = organize_by_groups
        # self.dry_run = dry_run
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

    def dump(self):
        if self.full:
            logger.report('Full set to True. Will overwrite previous directories.')
            _validate_make_dump_path(
                overwrite=True, validate_path=self.parent_path, logger=logger, safeguard_file=PROFILE_DUMP_JSON_FILE
            )

        # logger.report('Dumping groups...')

        self._dump_groups()

        logger.report('Dumping data nodes.')
        self._dump_data()

    def _dump_groups(self):
        # # ? These here relate to sorting by groups
        # self.group_sub_path = Path()

        profile_groups = QueryBuilder().append(Group).all(flat=True)
        # core_groups = [group for group in profile_groups if group.type_string == 'core']
        # import_groups = [group for group in profile_groups if group.type_string == 'core.import']
        non_import_groups = [group for group in profile_groups if not group.type_string.startswith('core.import')]
        # pseudo_groups = [group for group in profile_groups if group.type_string.startswith('pseudo')]

        # self.profile_groups = profile_groups

        for group in non_import_groups:
            group_subdir = Path(*group.type_string.split('.'))
            group_dumper = GroupDumper(parent_path=self.parent_path)
            # logger.report(
            #     f'self.parent_path / "groups" / group_subdir / group.label: {self.parent_path / group_subdir / group.label}'
            # )
            group_dumper.dump(
                group=group,
                output_path=self.parent_path / 'groups' / group_subdir / group.label,
            )

            # structures_path.mkdir(exist_ok=True, parents=True)

        # if self.organize_by_groups:
        #     LOGGER.report('Dumping sorted by groups.')
        #     for group in self.profile_groups:
        #         LOGGER.report(f'Dumping group: {group}')
        #         self.current_group = group
        #         self.group_sub_path = self.parent_path / 'groups' / Path(self.current_group.label)
        #         self.resolve_dump_entities()
        # else:
        #     self.resolve_dump_entities()

        # self.update_info_file()

        # print('hello from dump')
        # print('self.entity_counter_dictionary', self.entity_counter_dictionary)

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
        # ? Possibly do this by default?
        if Profile in self.entities_to_dump:
            self.dump_profile_info()

    def dump_structures(self, format: str = 'cif'):
        structure_datas = get_nodes_from_db(aiida_node_type=StructureData, with_group=self.current_group)

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
                    self.entities_to_dump
                # This is basically a FileExistsError
                except OSError:
                    continue

    def dump_workflows(self, only_parents: bool = True):
        # ? Dump only top-level workchains, as that includes sub-workchains already

        if self.organize_by_groups:
            workflows = get_nodes_from_db(aiida_node_type=WorkflowNode, with_group=self.current_group)
        else:
            workflows = get_nodes_from_db(aiida_node_type=WorkflowNode)

        for iworkflow_, workflow_ in enumerate(workflows):
            workflow = workflow_[0]

            if only_parents and workflow.caller is not None:
                continue

            workflow_dumper = ProcessDumper(**self.process_dumper_kwargs, overwrite=self.full)

            workflow_dump_path = (
                self.parent_path
                / self.group_sub_path
                / ProcessDumper._generate_default_dump_path(process_node=workflow)
            )

            if not self.dry_run:
                with contextlib.suppress(FileExistsError):
                    workflow_dumper.dump(process_node=workflow, output_path=workflow_dump_path)

            self.entity_counter_dictionary[WorkflowNode.__name__] += 1

            # To make development quicker
            if iworkflow_ > 1:
                break

    def dump_code_computers(self):
        computers = get_nodes_from_db(aiida_node_type=Computer, flat=True)

        computer_parent_path = self.parent_path / Path('computers')
        computer_parent_path.mkdir(parents=True, exist_ok=True)

        for computer in computers:
            computer_setup_file = computer_parent_path / f'{computer.label}-setup.yaml'
            # ? Copied over from `cmd_computer` as importing `computer_export_setup` led to click Context error:
            # TypeError: Context.__init__() got an unexpected keyword argument 'computer'
            computer_setup = {
                'label': computer.label,
                'hostname': computer.hostname,
                'description': computer.description,
                'transport': computer.transport_type,
                'scheduler': computer.scheduler_type,
                'shebang': computer.get_shebang(),
                'work_dir': computer.get_workdir(),
                'mpirun_command': ' '.join(computer.get_mpirun_command()),
                'mpiprocs_per_machine': computer.get_default_mpiprocs_per_machine(),
                'default_memory_per_machine': computer.get_default_memory_per_machine(),
                'use_double_quotes': computer.get_use_double_quotes(),
                'prepend_text': computer.get_prepend_text(),
                'append_text': computer.get_append_text(),
            }

            if not computer_setup_file.is_file():
                computer_setup_file.write_text(yaml.dump(computer_setup, sort_keys=False), 'utf-8')

            computer_config_file = computer_parent_path / f'{computer.label}-config.yaml'

            from aiida.orm import User

            users = User.collection.all()
            for user in users:
                computer_configuration = computer.get_configuration(user)
                if not computer_config_file.is_file():
                    computer_config_file.write_text(yaml.dump(computer_configuration, sort_keys=False), 'utf-8')

        codes = get_nodes_from_db(aiida_node_type=Code, flat=True)

        code_parent_path = self.parent_path / Path('codes')
        code_parent_path.mkdir(parents=True, exist_ok=True)

        for code in codes:
            code_file = code_parent_path / f'{code.label}.yaml'
            code_data = {}

            # ? Copied over from `cmd_code`
            # ? In some cases, `verdi code export` does not contain the relevant `Computer` attached to it
            for key in code.Model.model_fields.keys():
                value = getattr(code, key).label if key == 'computer' else getattr(code, key)

                if value is not None:
                    code_data[key] = str(value)

            if not code_file.is_file():
                code_file.write_text(yaml.dump(code_data, sort_keys=False), 'utf-8')

    def dump_user_info(self):
        pass

    def node_exists_on_disk(self):
        pass

    def dump_calculations(self):
        pass

    def _dump_data(self):
        # logger.report(f'entity_counter: {self.entity_counter}')

        self.entity_counter = CollectionDumper.create_entity_counter()

        for data_class in DEFAULT_DATA_TO_DUMP:
            # ? Could also do try/except, as key only in `entity_counter` when instances of type in group
            if self.entity_counter.get(data_class, 0) > 0:
                # logger.report(data_class)
                data_nodes = get_nodes_from_db(aiida_node_type=data_class, flat=True)
                for data_node in data_nodes:
                    # logger.report(f'{type(data_node)}: {data_node}')
                    # logger.report(f'{isinstance(data_node, orm.StructureData)}')

                    datadumper = DataDumper(overwrite=True)

                    # Must pass them implicitly here, rather than, e.g. `data_node=data_node`
                    # Otherwise `singledispatch` raises: `IndexError: tuple index out of range`
                    datadumper.dump(data_node, self.parent_path)

                # print(data_nodes)


