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

import logging
import typing as t
from logging import Logger
from pathlib import Path

from rich.console import Console
from rich.table import Table

__all__ = ('validate_make_dump_path', 'get_nodes_from_db')

logger = logging.getLogger(__name__)


def validate_make_dump_path(
    overwrite: bool,
    path_to_validate: Path,
    logger: Logger | None = None,
    safeguard_file: str | None = '.aiida_node_metadata.yaml',
    enforce_safeguard: bool = True,
) -> Path:
    """Create default dumping directory for a given process node and return it as absolute path.

    :param validate_path: Path to validate for dumping.
    :param safeguard_file: Dumping-specific file to avoid deleting wrong directory.
        Default: `.aiida_node_metadata.yaml`
    :return: The absolute created dump path.
    """
    import shutil

    if path_to_validate.is_dir():
        # Existing, empty directory -> OK
        if not any(path_to_validate.iterdir()):
            pass

        # Existing, non-empty directory and overwrite False -> FileExistsError
        elif not overwrite:
            raise FileExistsError(f'Path `{path_to_validate}` already exists and overwrite set to False.')

        # Existing, non-empty directory and overwrite True
        # Check for safeguard file ('.aiida_node_metadata.yaml') for safety
        # If present -> Remove directory
        elif enforce_safeguard and safeguard_file is not None:
            if (path_to_validate / safeguard_file).is_file():
                if logger is not None:
                    logger.info(f'Overwrite set to true, will overwrite directory `{path_to_validate}`.')
                shutil.rmtree(path_to_validate)

            else:
                raise Exception(
                    f"Path `{path_to_validate}` already exists and doesn't contain safeguard file {safeguard_file}."
                    f' Not removing for safety reasons. Delete manually.'
                )

        elif enforce_safeguard and safeguard_file is None:
            raise Exception('Safeguard enforced  but no safeguard_file provided. Must provide safeguard file.')

        # Existing and non-empty directory and overwrite True
        # Check for safeguard file ('.aiida_node_metadata.yaml') for safety
        # If absent -> Don't remove directory as to not accidentally remove a wrong one
        else:
            raise Exception(
                f"Path `{path_to_validate}` already exists and doesn't contain safeguard file {safeguard_file}."
                f' Not removing for safety reasons.'
            )

    # Not included in if-else as to avoid having to repeat the `mkdir` call.
    # `exist_ok=True` as checks implemented above
    path_to_validate.mkdir(exist_ok=True, parents=True)

    return path_to_validate.resolve()


def get_nodes_from_db(qb_instance, qb_filters: t.List | None = None, flat=False):
    # Computers cannot be associated via `with_group`
    # for qb_filter in qb_filters:
    #     qb.add_filter(**qb_filter)

    return_iterable = qb_instance.iterall() if qb_instance.count() > 10 ^ 3 else qb_instance.all()

    # Manual flattening as `iterall` doesn't have `flat` option unlike `all`
    if flat:
        return_iterable = [_[0] for _ in return_iterable]

    return return_iterable


# def validate_rich_options(rich_options, rich_config_file):
#     if rich_options is not None and rich_config_file is not None:
#         raise ValueError('Specify rich options either via CLI or config file, not both.')

#     else:
#         logger.report('Neither `--rich-options` nor `--rich-config` set, using defaults.')


@staticmethod
def dumper_pretty_print(dumper_instance, include_private_and_dunder: bool = False):

    console = Console()
    table = Table(title=f'Attributes and Methods of {dumper_instance.__class__.__name__}')

    # Adding columns to the table
    table.add_column('Name', justify='left')
    table.add_column('Type', justify='left')
    table.add_column('Value', justify='left')

    # Lists to store attributes and methods
    entries = []

    # Iterate over the class attributes and methods
    for attr_name in dir(dumper_instance):
        # Exclude private attributes and dunder methods
        attr_value = getattr(dumper_instance, attr_name)
        entry_type = 'Attribute' if not callable(attr_value) else 'Method'

        if attr_name.startswith('_'):
            if include_private_and_dunder:
                entries.append((attr_name, entry_type, str(attr_value)))
            else:
                pass
        else:
            entries.append((attr_name, entry_type, str(attr_value)))

    # Sort entries: attributes first, then methods
    entries.sort(key=lambda x: (x[1] == 'Method', x[0]))

    # Add sorted entries to the table
    for name, entry_type, value in entries:
        table.add_row(name, entry_type, value)

    # Print the formatted table
    console.print(table)


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
