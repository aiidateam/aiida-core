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

import logging
from functools import singledispatchmethod
from pathlib import Path

import yaml

from aiida import orm
from aiida.cmdline.commands.cmd_data.cmd_export import data_export
from aiida.tools.dumping.abstract import AbstractDumper
from aiida.tools.dumping.rich import DEFAULT_CORE_EXPORT_MAPPING

logger = logging.getLogger(__name__)


class DataDumper(AbstractDumper):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def generate_output_name(self):
        pass

    # def dump(self, *args, **kwargs):
    #     data_export(*args, **kwargs)

    @singledispatchmethod
    def dump_rich_core(self, data_node, output_path):
        # raise NotImplementedError(f'Dumping not implemented for type {type(data_node)}')
        # print(f'No specific handler found for type <{type(data_node)}> <{data_node}>, doing nothing.')
        # output_path /= 'general'
        output_path.mkdir(exist_ok=True, parents=True)
        # This is effectively the `rich` dumping
        data_node_entry_point_name = data_node.entry_point.name
        try:
            export_settings = DEFAULT_CORE_EXPORT_MAPPING[data_node_entry_point_name]
            exporter = export_settings['exporter']
            fileformat = export_settings['export_format']
            output_fname = output_path / f'{data_node.__class__.__name__}-{data_node.pk}.{fileformat}'
            exporter(
                node=data_node,
                output_fname=output_fname,
                fileformat=fileformat,
                overwrite=self.overwrite,
            )
        # This is for orm.Data types for which no default dumping is implemented, e.g. Bool or Float
        except ValueError:
            pass
        # This is for orm.Data types for whose entry_point names no entry exists in the DEFAULT_CORE_EXPORT_MAPPING
        # This is now captured outside in the `CollectionDumper`, so should not be relevant anymore
        except TypeError:
            raise

    @dump_rich_core.register
    def _(self, data_node: orm.StructureData, output_path: str | Path | None = None):
        if type(data_node) is orm.StructureData:
            self._dump_structuredata(data_node, output_path=output_path)
        else:
            # Handle the case where data_node is a subclass of orm.StructureData
            # Just use the default dispatch function implementation
            self.dump_rich_core.dispatch(object)(self, data_node, output_path)

    @dump_rich_core.register
    def _(
        self,
        data_node: orm.Code,
        output_path: str | Path | None = None,
    ):
        self._dump_code(data_node=data_node, output_path=output_path)

    @dump_rich_core.register
    def _(
        self,
        data_node: orm.Computer,
        output_path: str | Path | None = None,
    ):
        self._dump_computer(data_node=data_node, output_path=output_path)

    @dump_rich_core.register
    def _(
        self,
        data_node: orm.BandsData,
        output_path: str | Path | None = None,
    ):
        self._dump_bandsdata(data_node=data_node, output_path=output_path)

    @dump_rich_core.register
    def _(
        self,
        data_node: orm.TrajectoryData,
        output_path: str | Path | None = None,
    ):
        self._dump_trajectorydata(data_node=data_node, output_path=output_path)

    @dump_rich_core.register
    def _(
        self,
        data_node: orm.UpfData,
        output_path: str | Path | None = None,
    ):
        self._dump_upfdata(data_node=data_node, output_path=output_path)

    def _dump_structuredata(
        self, data_node: orm.StructureData, output_path: Path | None = None, fileformat: str = 'cif'
    ):
        from aiida.common.exceptions import UnsupportedSpeciesError

        # ? There also exists a CifData file type
        # output_path /= 'structures'
        output_path.mkdir(exist_ok=True, parents=True)
        output_fname = output_path / f'{data_node.get_formula()}-{data_node.pk}.{fileformat}'
        try:
            data_export(
                node=data_node,
                output_fname=output_fname,
                fileformat=fileformat,
                overwrite=self.overwrite,
            )
        except UnsupportedSpeciesError:
            # This is the case for, e.g. HubbardStructureData that has species like `Mn0`
            # Not sure how to resolve this. Wouldn't add a singledispatch for data types defined in plugins. Currently,
            # do strict type check. HubbardStructureData doesn't implement an export method itself, though.
            pass

    def _dump_code(
        self,
        data_node: orm.Code,
        output_path: Path | None = None,
        fileformat: str = 'yaml',
    ):
        # output_path /= 'codes'
        if fileformat != 'yaml':
            raise NotImplementedError('No other fileformats supported so far apart from YAML.')
        output_path.mkdir(exist_ok=True, parents=True)
        output_fname = output_path / f'{data_node.full_label}-{data_node.pk}.{fileformat}'
        data_export(
            node=data_node,
            output_fname=output_fname,
            fileformat=fileformat,
            overwrite=self.overwrite,
        )

    def _dump_computer(self, data_node: orm.Computer, output_path: Path | None = None, fileformat: str = 'yaml'):
        # output_path /= 'computers'
        if fileformat != 'yaml':
            raise NotImplementedError('No other fileformats supported so far apart from YAML.')

        output_path.mkdir(exist_ok=True, parents=True)
        computer_setup_fname = output_path / f'{data_node.full_label}-setup-{data_node.pk}.{fileformat}'
        computer_config_fname = output_path / f'{data_node.full_label}-config-{data_node.pk}.{fileformat}'

        # ? Copied over from `cmd_computer` as importing `computer_export_setup` led to click Context error:
        # TypeError: Context.__init__() got an unexpected keyword argument 'computer'
        computer_setup = {
            'label': data_node.label,
            'hostname': data_node.hostname,
            'description': data_node.description,
            'transport': data_node.transport_type,
            'scheduler': data_node.scheduler_type,
            'shebang': data_node.get_shebang(),
            'work_dir': data_node.get_workdir(),
            'mpirun_command': ' '.join(data_node.get_mpirun_command()),
            'mpiprocs_per_machine': data_node.get_default_mpiprocs_per_machine(),
            'default_memory_per_machine': data_node.get_default_memory_per_machine(),
            'use_double_quotes': data_node.get_use_double_quotes(),
            'prepend_text': data_node.get_prepend_text(),
            'append_text': data_node.get_append_text(),
        }

        if not computer_setup_fname.is_file():
            computer_setup_fname.write_text(yaml.dump(computer_setup, sort_keys=False), 'utf-8')

        from aiida.orm import User

        users = User.collection.all()
        for user in users:
            computer_configuration = data_node.get_configuration(user)
            if not computer_config_fname.is_file():
                computer_config_fname.write_text(yaml.dump(computer_configuration, sort_keys=False), 'utf-8')

    def _dump_bandsdata(self, data_node: orm.BandsData, output_path: Path | None = None, fileformat: str = 'mpl_pdf'):
        # ? There also exists a CifData file type
        # output_path /= 'bandstructures'
        output_path.mkdir(exist_ok=True, parents=True)
        # print(f'FILEFORMAT: {fileformat}')
        if fileformat == 'mpl_pdf':
            fileextension = 'pdf'
        output_fname = output_path / f'{data_node.__class__.__name__}-{data_node.pk}.{fileextension}'
        data_export(
            node=data_node,
            output_fname=output_fname,
            fileformat=fileformat,
            overwrite=self.overwrite,
        )

    def _dump_trajectorydata(
        self,
        data_node: orm.TrajectoryData,
        output_path: Path | None = None,
        fileformat: str = 'cif',
    ):
        # ? There also exists a CifData file type
        # output_path /= 'trajectories'
        output_path.mkdir(exist_ok=True, parents=True)
        output_fname = output_path / f'{data_node.__class__.__name__}-{data_node.pk}.{fileformat}'
        data_export(
            node=data_node,
            output_fname=output_fname,
            fileformat=fileformat,
            overwrite=self.overwrite,
        )

    def _dump_user_info(self): ...

    def dump_raw(self):
        pass
