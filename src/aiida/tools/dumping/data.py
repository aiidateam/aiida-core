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
from pathlib import Path
import logging
import yaml
from aiida.tools.dumping.abstract import AbstractDumper
from aiida.cmdline.commands.cmd_data.cmd_export import data_export

logger = logging.getLogger(__name__)


class DataDumper(AbstractDumper):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def generate_output_name(self):
        pass

    def dump(self, *args, **kwargs):
        data_export(*args, **kwargs)

    # @singledispatchmethod
    # def dump(self, data_node, output_path):
    #     # raise NotImplementedError(f'Dumping not implemented for type {type(data_node)}')
    #     print(f'No specific handler found for type <{type(data_node)}> <{data_node}>, doing nothing.')

    # @dump.register
    # def _(self, data_node: orm.StructureData, output_path: str | Path | None = None):
    #     print(f'self, data_node, output_path{self, data_node, output_path}')
    #     self._dump_structuredata(data_node=data_node, output_path=output_path)

    # @dump.register
    # def _(self, data_node: orm.AbstractCode, output_path: str | Path | None = None):
    #     self._dump_code(data_node=data_node, output_path=output_path)

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

    # def _dump_structuredata(
    #     self,
    #     data_node: orm.StructureData,
    #     output_path: Path | None = None,
    # ):
    #     # ? There also exists a CifData file type

    #     if output_path is None:
    #         output_path = Path.cwd()

    #     output_path /= 'structures'

    #     output_path.mkdir(exist_ok=True, parents=True)

    #     file_name = f'{data_node.get_formula()}-{data_node.pk}.cif'

    #     try:
    #         data_node.export(path=output_path / file_name, fileformat='cif', overwrite=True)
    #     except OSError as exc:
    #         raise exc

    # @staticmethod
    # def _dump_code(
    #     # ? Should have same signature as `data_export function
    #     data_node: orm.AbstractCode,
    #     output_path: Path | None = None,
    #     file_name: str | Path | None = None,
    #     file_format: str = 'yaml',
    #     *args,
    #     **kwargs
    # ):
    #     if output_path is None:
    #         output_path = Path.cwd()
    #     # output_path /= 'codes'

    #     output_path.mkdir(exist_ok=True, parents=True)

    #     code_data = {}

    #     # ? Copied over from `cmd_code`
    #     # ? In some cases, `verdi code export` does not contain the relevant `Computer` attached to it
    #     for key in data_node.Model.model_fields.keys():
    #         value = getattr(data_node, key).label if key == 'computer' else getattr(data_node, key)

    #         if value is not None:
    #             code_data[key] = str(value)
    #     if file_name is None:
    #         try:
    #             file_name = f"{code_data['label']}@{code_data['computer']}.{file_format}"
    #         except KeyError:
    #             file_name = f"{code_data['label']}.{file_format}"

    #     code_file = output_path / file_name

    #     if not code_file.is_file():
    #         code_file.write_text(yaml.dump(code_data, sort_keys=False), 'utf-8')

    def _dump_user_info(self): ...
