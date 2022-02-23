# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
# pylint: disable=cell-var-from-loop
"""Utility functions for command line commands for developers."""

from pathlib import Path
import re

from aiida.plugins.entry_point import DEPRECATED_ENTRY_POINTS_MAPPING, FACTORY_MAPPING


def migrate_path(path: Path):
    """Recursively migrate ``.py``, ``.rst`` and ``.md`` files in ``path`` ``aiida-core`` v2.0"""

    if path.is_dir():
        for sub_path in path.iterdir():
            migrate_path(sub_path)

    elif path.suffix in ['.py', '.rst', '.md']:
        with path.open('r') as handle:
            contents = handle.read()

        contents = migrate_entry_points(contents)
        contents = migrate_dict_list(contents)

        with path.open('w') as handle:
            handle.write(contents)


def migrate_entry_points(contents: str) -> str:
    """Add ``core.`` prefix to deprecated entry points."""

    for entry_point_group, entry_points in DEPRECATED_ENTRY_POINTS_MAPPING.items():

        sub_string = '|'.join(entry_points)

        # Loading classes from factories
        factory = FACTORY_MAPPING[entry_point_group]
        factory_name = factory.__name__

        def add_core_factory(matchobj):
            return f"{factory_name}('core.{matchobj.groups()[0]}')"

        pattern_factory = fr"{factory_name}\('({sub_string})'\)"

        contents = re.sub(pattern_factory, add_core_factory, contents)

        # Full entry point specifications from group
        def add_core_group(matchobj):
            return f"'{entry_point_group}:core.{matchobj.groups()[0]}'"

        pattern_group = fr"'{entry_point_group}:({sub_string})'"

        contents = re.sub(pattern_group, add_core_group, contents)

        # Node types
        for entry_point in entry_points:
            class_name = factory(f'core.{entry_point}').__name__

            def add_core_type(matchobj):
                return f"{entry_point_group.rsplit('.', maxsplit=1)[-1]}.core.{matchobj.groups()[0]}.{class_name}."

            pattern_type = fr"{entry_point_group.rsplit('.', maxsplit=1)[-1]}\.({entry_point})\.{class_name}\."

            contents = re.sub(pattern_type, add_core_type, contents)

        # `verdi plugin list` commands
        def add_core_plugin(matchobj):
            return f'verdi plugin list {entry_point_group} core.{matchobj.groups()[0]}'

        pattern_plugin = fr'verdi\splugin\slist\s{entry_point_group}\s({sub_string})'

        contents = re.sub(pattern_plugin, add_core_plugin, contents)

    return contents


def migrate_dict_list(contents: str) -> str:
    """Remove ``dict`` and ``list`` keyword arguments from ``Dict`` and ``List`` initializations."""

    def remove_dict_kw(matchobj):
        return f'Dict({matchobj.groups()[0]}'

    pattern_dict = r'Dict\(([\s\n]*)dict='

    contents = re.sub(pattern_dict, remove_dict_kw, contents)

    def remove_list_kw(matchobj):
        return f'List({matchobj.groups()[0]}'

    pattern_list = r'List\(([\s\n]*)list='

    contents = re.sub(pattern_list, remove_list_kw, contents)

    return contents
