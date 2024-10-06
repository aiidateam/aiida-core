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
from aiida.cmdline.params.types import FileOrUrl

logger = logging.getLogger(__name__)


class DataDumper:
    def __init__(
        self,
        *args,
        overwrite: bool = False,
        also_raw: bool = False,
        also_rich: bool = False,
        rich_options: str = '',
        rich_config_file: FileOrUrl | None = None,
        rich_dump_all: bool = True,
        rich_use_defaults: bool = True,
        **kwargs,
    ) -> None:
        # super().__init__(*args, **kwargs)
        self.args = args
        self.overwrite = overwrite
        self.also_raw = also_raw
        self.also_rich = also_rich
        self.rich_options = rich_options
        self.rich_config_file = rich_config_file
        self.rich_dump_all = rich_dump_all
        self.rich_use_defaults = rich_use_defaults
        self.kwargs = kwargs

    @singledispatchmethod
    def dump_rich_core(self, data_node, rich_options_dict, output_path, output_fname):
        # raise NotImplementedError(f'Dumping not implemented for type {type(data_node)}')
        # print(f'No specific handler found for type <{type(data_node)}> <{data_node}>, doing nothing.')
        # output_path /= 'general'
        output_path.mkdir(exist_ok=True, parents=True)
        # This is effectively the `rich` dumping
        data_node_entry_point_name = data_node.entry_point.name
        try:
            export_settings = rich_options_dict[data_node_entry_point_name]
            exporter = export_settings['exporter']
            fileformat = export_settings['export_format']

            exporter(
                node=data_node,
                output_fname=output_path / output_fname,
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
    def _(
        self,
        data_node: orm.StructureData,
        rich_options_dict: dict,
        output_path: str | Path | None = None,
        output_fname: str | None = None,
    ):
        if type(data_node) is orm.StructureData:
            self._dump_structuredata(
                data_node, output_path=output_path, output_fname=output_fname, rich_options_dict=rich_options_dict
            )
        else:
            # Handle the case where data_node is a subclass of orm.StructureData
            # Just use the default dispatch function implementation
            self.dump_rich_core.dispatch(object)(self, data_node, rich_options_dict, output_path, output_fname)

    @dump_rich_core.register
    def _(
        self,
        data_node: orm.Code,
        rich_options_dict: dict,
        output_path: str | Path | None = None,
        output_fname: str | None = None,
    ):
        self._dump_code(
            data_node=data_node, output_path=output_path, output_fname=output_fname, rich_options_dict=rich_options_dict
        )

    @dump_rich_core.register
    def _(
        self,
        data_node: orm.Computer,
        rich_options_dict: dict,
        output_path: str | Path | None = None,
        output_fname: str | None = None,
    ):
        self._dump_computer_setup(
            data_node=data_node, output_path=output_path, output_fname=output_fname, rich_options_dict=rich_options_dict
        )
        self._dump_computer_config(
            data_node=data_node, output_path=output_path, output_fname=output_fname, rich_options_dict=rich_options_dict
        )

    @dump_rich_core.register
    def _(
        self,
        data_node: orm.BandsData,
        rich_options_dict: dict,
        output_path: str | Path | None = None,
        output_fname: str | None = None,
    ):
        self._dump_bandsdata(
            data_node=data_node, output_path=output_path, output_fname=output_fname, rich_options_dict=rich_options_dict
        )

    # These are the rich dumping implementations that actually differ from the default dispatch
    def _dump_structuredata(
        self,
        data_node: orm.StructureData,
        rich_options_dict: dict,
        output_path: Path | None = None,
        output_fname: str | None = None,
        fileformat: str | None = 'cif',
    ):
        from aiida.common.exceptions import UnsupportedSpeciesError

        if output_fname is None:
            output_fname = DataDumper.generate_output_fname_rich(
                data_node=data_node, fileformat=fileformat, rich_options_dict=rich_options_dict
            )

        # ? There also exists a CifData file type
        # output_path /= 'structures'
        output_path.mkdir(exist_ok=True, parents=True)
        try:
            node_entry_point_name = data_node.entry_point.name
            exporter = rich_options_dict[node_entry_point_name]['exporter']
            fileformat = rich_options_dict[node_entry_point_name]['export_format']

            exporter(
                node=data_node,
                output_fname=output_path / output_fname,
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
        rich_options_dict: dict,
        output_path: Path | None = None,
        output_fname: str | None = None,
    ):
        # output_path /= 'codes'

        node_entry_point_name = data_node.entry_point.name
        exporter = rich_options_dict[node_entry_point_name]['exporter']
        fileformat = rich_options_dict[node_entry_point_name]['export_format']

        if fileformat != 'yaml':
            raise NotImplementedError('No other fileformats supported so far apart from YAML.')
        output_path.mkdir(exist_ok=True, parents=True)
        if output_fname is None:
            output_fname = DataDumper.generate_output_fname_rich(data_node=data_node, fileformat=fileformat)

        exporter(
            node=data_node,
            output_fname=output_path / output_fname,
            fileformat=fileformat,
            overwrite=self.overwrite,
        )

    def _dump_computer_setup(
        self,
        data_node: orm.Computer,
        rich_options_dict: dict,
        output_path: Path | None = None,
        output_fname: str | None = None,
        fileformat: str = 'yaml',
    ):
        node_entry_point_name = data_node.entry_point.name
        # TODO: Don't use the `exporter` here, as `Computer` doesn't derive from Data, so custom implementation
        # exporter = rich_options_dict[node_entry_point_name]['exporter']
        fileformat = rich_options_dict[node_entry_point_name]['export_format']

        if fileformat != 'yaml':
            raise NotImplementedError('No other fileformats supported so far apart from YAML.')

        output_path.mkdir(exist_ok=True, parents=True)

        # This is a bit of a hack. Should split this up into two different functions.
        if output_fname is None:
            output_fname = output_path / f'{data_node.full_label}-setup-{data_node.pk}.{fileformat}'

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

        if not output_fname.is_file():
            output_fname.write_text(yaml.dump(computer_setup, sort_keys=False), 'utf-8')

    def _dump_computer_config(
        self,
        data_node: orm.Computer,
        rich_options_dict: dict,
        output_path: Path | None = None,
        output_fname: str | None = None,
    ):
        from aiida.orm import User

        node_entry_point_name = data_node.entry_point.name
        # TODO: Don't use the `exporter` here, as `Computer` doesn't derive from Data, so custom implementation
        # exporter = rich_options_dict[node_entry_point_name]['exporter']
        fileformat = rich_options_dict[node_entry_point_name]['export_format']

        # output_path /= 'computers'
        if fileformat != 'yaml':
            raise NotImplementedError('No other fileformats supported so far apart from YAML.')

        output_path.mkdir(exist_ok=True, parents=True)

        # This is a bit of a hack. Should split this up into two different functions.
        if output_fname is None:
            output_fname = output_path / f'{data_node.full_label}-config-{data_node.pk}.{fileformat}'

        users = User.collection.all()
        for user in users:
            computer_configuration = data_node.get_configuration(user)
            if not output_fname.is_file():
                output_fname.write_text(yaml.dump(computer_configuration, sort_keys=False), 'utf-8')

    def _dump_bandsdata(
        self,
        data_node: orm.BandsData,
        rich_options_dict: dict,
        output_path: Path | None = None,
        output_fname: str | None = None,
    ):
        node_entry_point_name = data_node.entry_point.name
        exporter = rich_options_dict[node_entry_point_name]['exporter']
        fileformat = rich_options_dict[node_entry_point_name]['export_format']

        output_path.mkdir(exist_ok=True, parents=True)

        if output_fname is None:
            output_fname = DataDumper.generate_output_fname_rich(data_node=data_node, fileformat=fileformat)
        output_fname = output_fname.replace('mpl_pdf', 'pdf')

        exporter(
            node=data_node,
            output_fname=output_path / output_fname,
            fileformat=fileformat,
            overwrite=self.overwrite,
        )

    def _dump_user_info(self): ...

    def dump_raw(self, data_node: orm.Data, output_path: Path, output_fname: str | None = None):
        output_path.mkdir(exist_ok=True, parents=True)

        if output_fname is None:
            output_fname = DataDumper.generate_output_fname_raw(data_node=data_node)

        with open(output_path.resolve() / output_fname, 'w') as handle:
            yaml.dump(data_node.attributes, handle)

    @staticmethod
    def generate_output_fname_raw(data_node, prefix: str | None = None):
        if prefix is None:
            return f'{data_node.__class__.__name__}-{data_node.pk}_attrs.yaml'
        else:
            return f'{prefix}-{data_node.__class__.__name__}-{data_node.pk}_attrs.yaml'

    @staticmethod
    def generate_output_fname_rich(data_node, fileformat, prefix: str | None = None):
        if prefix is None:
            return f'{data_node.__class__.__name__}-{data_node.pk}.{fileformat}'
        else:
            return f'{prefix}-{data_node.__class__.__name__}-{data_node.pk}.{fileformat}'
