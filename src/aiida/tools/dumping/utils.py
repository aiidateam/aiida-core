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
from datetime import datetime
from pathlib import Path

from aiida import orm
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


def sanitize_file_extension(filename: str | Path):
    if isinstance(filename, Path):
        filename = str(filename)
    if filename.endswith('.mpl_pdf'):
        filename = filename.replace('.mpl_pdf', '.pdf')
    if filename.endswith('.mpl_png'):
        filename = filename.replace('.mpl_png', '.png')

    return Path(filename)


def filter_by_last_dump_time(nodes: list[str], last_dump_time: datetime | None = None) -> list[str]:
    if last_dump_time is not None:
        orm_nodes = [orm.load_node(node) for node in nodes]
        return [node.uuid for node in orm_nodes if node.mtime > last_dump_time]
    else:
        return nodes
