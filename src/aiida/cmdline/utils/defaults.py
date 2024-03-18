###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Default values and lazy default get methods for command line options."""

from pathlib import Path
from typing import Union

from aiida.cmdline.utils import echo
from aiida.common import exceptions
from aiida.manage.configuration import get_config
from aiida.orm import CalcJobNode, WorkChainNode


def get_default_profile():
    """Try to get the name of the default profile.

    This utility function should only be used for defaults or callbacks in command line interface parameters.
    Otherwise, the preference should go to calling `get_config` to load the actual config and using
    `config.default_profile_name` to get the default profile name.

    :raises click.UsageError: if the config could not be loaded or no default profile exists
    :return: the default profile name or None if no default is defined in the configuration
    """
    try:
        config = get_config(create=True)
    except exceptions.ConfigurationError as exception:
        echo.echo_critical(str(exception))

    try:
        default_profile = config.get_profile(config.default_profile_name).name
    except exceptions.ProfileConfigurationError:
        default_profile = None

    return default_profile


def make_default_dump_path(
    process_node: Union[WorkChainNode, CalcJobNode], path: Path = Path(), overwrite: bool = False
):
    """
    Create default dumping directory for a given process node.

    :param process_node: The `ProcessNode` for which the directory is created.
    :type process_node: Union[WorkChainNode, CalcJobNode]
    :param path: The base path for the dump. Defaults to the current directory.
    :type path: Path
    :return: The created dump path.
    :rtype: Path
    """
    import shutil

    if str(path) == '.':
        path = Path(f'dump-{process_node.uuid[:8]}')

    if path.is_dir():
        if overwrite:
            echo.echo_report(f'Overwrite set to true, will overwrite directory "{path}".')
            shutil.rmtree(path)
        else:
            echo.echo_critical(f'Invalid dumping destination selected. Path: "{path}" already exists.')
    path.mkdir(parents=True, exist_ok=False)

    return path
