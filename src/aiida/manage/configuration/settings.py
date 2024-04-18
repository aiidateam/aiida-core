###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Base settings required for the configuration of an AiiDA instance."""

from __future__ import annotations

import os
import pathlib
import warnings

DEFAULT_UMASK = 0o0077
DEFAULT_AIIDA_PATH_VARIABLE = 'AIIDA_PATH'
DEFAULT_AIIDA_PATH = '~'
DEFAULT_AIIDA_USER = 'aiida@localhost'
DEFAULT_CONFIG_DIR_NAME = '.aiida'
DEFAULT_CONFIG_FILE_NAME = 'config.json'
DEFAULT_CONFIG_INDENT_SIZE = 4
DEFAULT_DAEMON_DIR_NAME = 'daemon'
DEFAULT_DAEMON_LOG_DIR_NAME = 'log'
DEFAULT_ACCESS_CONTROL_DIR_NAME = 'access'

# Assign defaults which may be overriden in set_configuration_directory() below
AIIDA_CONFIG_FOLDER: pathlib.Path = pathlib.Path(DEFAULT_AIIDA_PATH).expanduser() / DEFAULT_CONFIG_DIR_NAME
DAEMON_DIR: pathlib.Path = AIIDA_CONFIG_FOLDER / DEFAULT_DAEMON_DIR_NAME
DAEMON_LOG_DIR: pathlib.Path = DAEMON_DIR / DEFAULT_DAEMON_LOG_DIR_NAME
ACCESS_CONTROL_DIR: pathlib.Path = AIIDA_CONFIG_FOLDER / DEFAULT_ACCESS_CONTROL_DIR_NAME


def create_instance_directories() -> None:
    """Create the base directories required for a new AiiDA instance.

    This will create the base AiiDA directory defined by the AIIDA_CONFIG_FOLDER variable, unless it already exists.
    Subsequently, it will create the daemon directory within it and the daemon log directory.
    """
    from aiida.common import ConfigurationError

    directory_base = AIIDA_CONFIG_FOLDER.expanduser()
    directory_daemon = directory_base / DAEMON_DIR
    directory_daemon_log = directory_base / DAEMON_LOG_DIR
    directory_access = directory_base / ACCESS_CONTROL_DIR

    list_of_paths = [
        directory_base,
        directory_daemon,
        directory_daemon_log,
        directory_access,
    ]

    umask = os.umask(DEFAULT_UMASK)

    try:
        for path in list_of_paths:
            if path is directory_base and not path.exists():
                warnings.warn(f'Creating AiiDA configuration folder `{path}`.')

            try:
                path.mkdir(parents=True, exist_ok=True)
            except OSError as exc:
                raise ConfigurationError(f'could not create the `{path}` configuration directory: {exc}') from exc
    finally:
        os.umask(umask)


def get_configuration_directory():
    """Return the path of the configuration directory.

    The location of the configuration directory is defined following these heuristics in order:

        * If the ``AIIDA_PATH`` variable is set, all the paths will be checked to see if they contain a
          configuration folder. The first one to be encountered will be set as ``AIIDA_CONFIG_FOLDER``. If none of them
          contain one, the last path defined in the environment variable considered is used.
        * If an existing directory is still not found, the ``DEFAULT_AIIDA_PATH`` is used.

    :returns: The path of the configuration directory.
    """
    dirpath_config = get_configuration_directory_from_envvar()

    # If no existing configuration directory is found, fall back to the default
    if dirpath_config is None:
        dirpath_config = pathlib.Path(DEFAULT_AIIDA_PATH).expanduser() / DEFAULT_CONFIG_DIR_NAME

    return dirpath_config


def get_configuration_directory_from_envvar() -> pathlib.Path | None:
    """Return the path of a config directory from the ``AIIDA_PATH`` environment variable.

    The environment variable should be a colon separated string of filepaths that either point directly to a config
    directory or a path that contains a config directory. The first match is returned. If no existing config directory
    is found, the last path in the environment variable is used.

    :returns: The path of the configuration directory or ``None`` if ``AIIDA_PATH`` is not defined.
    """
    environment_variable = os.environ.get(DEFAULT_AIIDA_PATH_VARIABLE)

    if environment_variable is None:
        return None

    # Loop over all the paths in the ``AIIDA_PATH`` variable to see if any of them contain a configuration folder
    for base_dir_path in [path for path in environment_variable.split(':') if path]:
        dirpath_config = pathlib.Path(base_dir_path).expanduser()

        # Only add the base config directory name to the base path if it does not already do so
        # Someone might already include it in the environment variable. e.g.: ``AIIDA_PATH=/home/some/path/.aiida``
        if dirpath_config.name != DEFAULT_CONFIG_DIR_NAME:
            dirpath_config = dirpath_config / DEFAULT_CONFIG_DIR_NAME

        # If the directory exists, we leave it set and break the loop
        if dirpath_config.is_dir():
            break

    return dirpath_config


def set_configuration_directory(aiida_config_folder: pathlib.Path | None = None) -> None:
    """Set the configuration directory, related global variables and create instance directories.

    The location of the configuration directory is defined by ``aiida_config_folder`` or if not defined, the path that
    is returned by ``get_configuration_directory``. If the directory does not exist yet, it is created, together with
    all its subdirectories.
    """
    global AIIDA_CONFIG_FOLDER  # noqa: PLW0603
    global DAEMON_DIR  # noqa: PLW0603
    global DAEMON_LOG_DIR  # noqa: PLW0603
    global ACCESS_CONTROL_DIR  # noqa: PLW0603

    AIIDA_CONFIG_FOLDER = aiida_config_folder or get_configuration_directory()
    DAEMON_DIR = AIIDA_CONFIG_FOLDER / DEFAULT_DAEMON_DIR_NAME
    DAEMON_LOG_DIR = DAEMON_DIR / DEFAULT_DAEMON_LOG_DIR_NAME
    ACCESS_CONTROL_DIR = AIIDA_CONFIG_FOLDER / DEFAULT_ACCESS_CONTROL_DIR_NAME

    create_instance_directories()


# Initialize the configuration directory settings
set_configuration_directory()
