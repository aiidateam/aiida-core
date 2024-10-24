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

__all__ = ['validate_make_dump_path']

logger = logging.getLogger(__name__)


def validate_make_dump_path(
    path_to_validate: Path,
    overwrite: bool = False,
    incremental: bool = True,
    safeguard_file: str = '.aiida_node_metadata.yaml',
    enforce_safeguard: bool = True,
) -> Path:
    """Create default dumping directory for a given process node and return it as absolute path.

    :param validate_path: Path to validate for dumping.
    :param safeguard_file: Dumping-specific file to avoid deleting wrong directory.
        Default: `.aiida_node_metadata.yaml`
    :return: The absolute created dump path.
    """

    if overwrite and incremental:
        raise ValueError('Both overwrite and incremental set to True. Only specify one.')

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

        # Case 2: Non-empty directory, overwrite is True, enforce safeguard
        if not is_empty and overwrite:
            if enforce_safeguard and safeguard_file is None:
                raise Exception('Safeguard enforced but no safeguard_file provided. Must provide safeguard file.')

            safeguard_exists = (path_to_validate / safeguard_file).is_file()
            if enforce_safeguard and not safeguard_exists:
                raise Exception(
                    f'Path `{path_to_validate}` exists without safeguard file '
                    f'`{safeguard_file}`. Not removing for safety reasons.'
                )

            if safeguard_exists:
                logger.info(f'Overwriting directory `{path_to_validate}`.')
                shutil.rmtree(path_to_validate)

    # Create directory if it doesn't exist or was removed
    path_to_validate.mkdir(exist_ok=True, parents=True)

    return path_to_validate.resolve()
