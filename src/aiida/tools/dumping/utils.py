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
import shutil
from pathlib import Path

__all__ = ['_prepare_dump_path']

logger = logging.getLogger(__name__)


def _prepare_dump_path(
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
        raise ValueError('Both overwrite and incremental set to True. Only specify one.')

    if path_to_validate.is_file():
        raise FileExistsError(f'A file at the given path `{path_to_validate}` already exists.')

    # Handle existing directory
    if path_to_validate.is_dir():
        is_empty = not any(path_to_validate.iterdir())

        # Case 1: Non-empty directory and overwrite is False
        if not is_empty and not overwrite:
            if incremental:
                logger.info('Incremental dumping selected. Will keep directory.')
            else:
                raise FileExistsError(
                    f'Path `{path_to_validate}` already exists, and neither overwrite nor incremental is enabled.'
                )

        # Case 2: Non-empty directory, overwrite is True
        if not is_empty and overwrite:
            safeguard_exists = (path_to_validate / safeguard_file).is_file()

            if safeguard_exists:
                logger.info(f'Overwriting directory `{path_to_validate}`.')
                shutil.rmtree(path_to_validate)

            else:
                raise FileNotFoundError(
                    f'Path `{path_to_validate}` exists without safeguard file '
                    f'`{safeguard_file}`. Not removing because path might be a directory not created by AiiDA.'
                )

    # Create directory if it doesn't exist or was removed
    path_to_validate.mkdir(exist_ok=True, parents=True)
    (path_to_validate / safeguard_file).touch()
