###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Utility functions for dumping features."""

from __future__ import annotations

import shutil
from pathlib import Path

from aiida.common.log import AIIDA_LOGGER

__all__ = ['prepare_dump_path']

logger = AIIDA_LOGGER.getChild('tools.dumping')


def prepare_dump_path(
    path_to_validate: Path,
    overwrite: bool = False,
    incremental: bool = True,
    safeguard_file: str = '.aiida_node_metadata.yaml',
) -> None:
    """Create default dumping directory for a given process node and return it as absolute path.

    :param validate_path: Path to validate for dumping.
    :param safeguard_file: Dumping-specific file that indicates that the directory indeed originated from a `verdi ...
        dump` command to avoid accidentally deleting wrong directory.
        Default: `.aiida_node_metadata.yaml`
    :return: The absolute created dump path.
    :raises ValueError: If both `overwrite` and `incremental` are set to True.
    :raises FileExistsError: If a file or non-empty directory exists at the given path and none of `overwrite` or
        `incremental` are enabled.
    :raises FileNotFoundError: If no `safeguard_file` is found."""

    if overwrite and incremental:
        msg = 'Both overwrite and incremental set to True. Only specify one.'
        raise ValueError(msg)

    if path_to_validate.is_file():
        msg = f'A file at the given path `{path_to_validate}` already exists.'
        raise FileExistsError(msg)

    # Handle existing directory
    if path_to_validate.is_dir():
        is_empty = not any(path_to_validate.iterdir())

        # Case 1: Non-empty directory and overwrite is False
        if not is_empty and not overwrite:
            if incremental:
                msg = f'Incremental dumping selected. Will update directory `{path_to_validate}` with new data.'
                logger.report(msg)
            else:
                msg = f'Path `{path_to_validate}` already exists, and neither overwrite nor incremental is enabled.'
                raise FileExistsError(msg)

        # Case 2: Non-empty directory, overwrite is True
        if not is_empty and overwrite:
            safeguard_exists = (path_to_validate / safeguard_file).is_file()

            if safeguard_exists:
                msg = f'Overwriting directory `{path_to_validate}`.'
                logger.report(msg)
                shutil.rmtree(path_to_validate)

            else:
                msg = (
                    f'Path `{path_to_validate}` exists without safeguard file `{safeguard_file}`. '
                    f'Not removing because path might be a directory not created by AiiDA.'
                )
                raise FileNotFoundError(msg)

    # Create directory if it doesn't exist or was removed
    path_to_validate.mkdir(exist_ok=True, parents=True)
    (path_to_validate / safeguard_file).touch()


# @staticmethod
# def dumper_pretty_print(dumper_instance, include_private_and_dunder: bool = False):
#     console = Console()
#     table = Table(title=f'Attributes and Methods of {dumper_instance.__class__.__name__}')

#     # Adding columns to the table
#     table.add_column('Name', justify='left')
#     table.add_column('Type', justify='left')
#     table.add_column('Value', justify='left')

#     # Lists to store attributes and methods
#     entries = []

#     # Iterate over the class attributes and methods
#     for attr_name in dir(dumper_instance):
#         # Exclude private attributes and dunder methods
#         attr_value = getattr(dumper_instance, attr_name)
#         entry_type = 'Attribute' if not callable(attr_value) else 'Method'

#         if attr_name.startswith('_'):
#             if include_private_and_dunder:
#                 entries.append((attr_name, entry_type, str(attr_value)))
#             else:
#                 pass
#         else:
#             entries.append((attr_name, entry_type, str(attr_value)))

#     # Sort entries: attributes first, then methods
#     entries.sort(key=lambda x: (x[1] == 'Method', x[0]))

#     # Add sorted entries to the table
#     for name, entry_type, value in entries:
#         table.add_row(name, entry_type, value)

#     # Print the formatted table
#     console.print(table)


# def check_storage_size_user():
#     from aiida.manage.manager import get_manager

#     manager = get_manager()
#     storage = manager.get_profile_storage()

#     data = storage.get_info(detailed=True)
#     repository_data = data['repository']['Size (MB)']
#     total_size_gb = sum(repository_data.values()) / 1024
#     if total_size_gb > 10:
#         user_input = (
#             input('Repository size larger than 10gb. Do you still want to dump the profile data? (y/N): ')
#             .strip()
#             .lower()
#         )

#         if user_input != 'y':
#             sys.exit()


def sanitize_file_extension(filename: str | Path):
    if isinstance(filename, Path):
        filename = str(filename)
    if filename.endswith('.mpl_pdf'):
        filename = filename.replace('.mpl_pdf', '.pdf')
    if filename.endswith('.mpl_png'):
        filename = filename.replace('.mpl_png', '.png')

    return Path(filename)
