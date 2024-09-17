###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Functionality for dumping of Data nodes."""

from __future__ import annotations
from functools import singledispatchmethod

from aiida import orm
from aiida.orm.nodes.data.structure import StructureData
from pathlib import Path
import logging
import yaml


logger = logging.getLogger(__name__)


class DataDumper:
    def __init__(
        self,
        overwrite: bool = False,
    ) -> None:
        self.overwrite = overwrite  # ? Does this make sense here

    def generate_output_name(self):
        pass

    @singledispatchmethod
    def dump(self, data_node, output_path):
        # raise NotImplementedError(f'Dumping not implemented for type {type(data_node)}')
        print(f'No specific handler found for type <{type(data_node)}> <{data_node}>, doing nothing.')
        pass

    @dump.register
    def _(self, data_node: StructureData, output_path: str | Path | None = None):
        self._dump_structuredata(data_node=data_node, output_path=output_path)

    @dump.register
    def _(self, data_node: orm.AbstractCode, output_path: str | Path | None = None):
        self._dump_code(data_node=data_node, output_path=output_path)

    # @dump.register
    # def _(self, data_node: orm.AbstractCode, output_path: str | Path | None = None):
    #     self._dump_code(data_node=data_node, output_path=output_path)

    # elif isinstance(data_node, orm.FolderData):
    #     pass
    #     # self._dump_folderdata(output_path=output_path)

    # elif isinstance(data_node, orm.RemoteData):
    #     pass
    #     # self._dump_folderdata(output_path=output_path)

    # elif isinstance(data_node, orm.JsonableData):
    #     pass
    #     # self._dump_jsonable(output_path=output_path)

    def _dump_structuredata(
        self,
        data_node: orm.StructureData,
        output_path: Path | None = None,
        file_name: str | Path | None = None,
        file_format: str = 'cif',
    ):
        # ? There also exists a CifData file type

        if output_path is None:
            output_path = Path.cwd()

        output_path /= 'structures'

        output_path.mkdir(exist_ok=True, parents=True)

        if file_name is None:
            file_name = f'{data_node.get_formula()}-{data_node.pk}.{file_format}'

        try:
            data_node.export(path=output_path / file_name, fileformat=file_format, overwrite=True)
        except OSError as exc:
            raise exc

    @staticmethod
    def _dump_code(
        # ? Should have same signature as `data_export function
        data_node: orm.AbstractCode,
        output_path: Path | None = None,
        file_name: str | Path | None = None,
        file_format: str = 'yaml',
        *args,
        **kwargs
    ):
        if output_path is None:
            output_path = Path.cwd()
        # output_path /= 'codes'

        output_path.mkdir(exist_ok=True, parents=True)

        code_data = {}

        # ? Copied over from `cmd_code`
        # ? In some cases, `verdi code export` does not contain the relevant `Computer` attached to it
        for key in data_node.Model.model_fields.keys():
            value = getattr(data_node, key).label if key == 'computer' else getattr(data_node, key)

            if value is not None:
                code_data[key] = str(value)
        if file_name is None:
            try:
                file_name = f"{code_data['label']}@{code_data['computer']}.{file_format}"
            except KeyError:
                file_name = f"{code_data['label']}.{file_format}"

        code_file = output_path / file_name

        if not code_file.is_file():
            code_file.write_text(yaml.dump(code_data, sort_keys=False), 'utf-8')

    # def _dump_computer(self):
    #     # `Computer` not derived from orm.Data

    #     computers = get_nodes_from_db(aiida_node_type=Computer, flat=True)

    #     computer_parent_path = self.parent_path / Path('computers')
    #     computer_parent_path.mkdir(parents=True, exist_ok=True)

    #     for computer in computers:
    #         computer_setup_file = computer_parent_path / f'{computer.label}-setup.yaml'
    #         # ? Copied over from `cmd_computer` as importing `computer_export_setup` led to click Context error:
    #         # TypeError: Context.__init__() got an unexpected keyword argument 'computer'
    #         computer_setup = {
    #             'label': computer.label,
    #             'hostname': computer.hostname,
    #             'description': computer.description,
    #             'transport': computer.transport_type,
    #             'scheduler': computer.scheduler_type,
    #             'shebang': computer.get_shebang(),
    #             'work_dir': computer.get_workdir(),
    #             'mpirun_command': ' '.join(computer.get_mpirun_command()),
    #             'mpiprocs_per_machine': computer.get_default_mpiprocs_per_machine(),
    #             'default_memory_per_machine': computer.get_default_memory_per_machine(),
    #             'use_double_quotes': computer.get_use_double_quotes(),
    #             'prepend_text': computer.get_prepend_text(),
    #             'append_text': computer.get_append_text(),
    #         }

    #         if not computer_setup_file.is_file():
    #             computer_setup_file.write_text(yaml.dump(computer_setup, sort_keys=False), 'utf-8')

    #         computer_config_file = computer_parent_path / f'{computer.label}-config.yaml'

    #         from aiida.orm import User

    #         users = User.collection.all()
    #         for user in users:
    #             computer_configuration = computer.get_configuration(user)
    #             if not computer_config_file.is_file():
    #                 computer_config_file.write_text(yaml.dump(computer_configuration, sort_keys=False), 'utf-8')

    #     pass

    def _dump_user_info(self): ...
