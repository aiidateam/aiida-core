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
from typing import final

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
glb_aiida_config_folder: pathlib.Path = pathlib.Path(DEFAULT_AIIDA_PATH).expanduser() / DEFAULT_CONFIG_DIR_NAME

# DAEMON_DIR: pathlib.Path = glb_aiida_config_folder / DEFAULT_DAEMON_DIR_NAME
# DAEMON_LOG_DIR: pathlib.Path = DAEMON_DIR / DEFAULT_DAEMON_LOG_DIR_NAME
# ACCESS_CONTROL_DIR: pathlib.Path = glb_aiida_config_folder / DEFAULT_ACCESS_CONTROL_DIR_NAME

@final
class AiiDAConfigPathResolver:
    """Path resolver for getting daemon dir, daemon log dir ad access control dir location.

    If `config_folder` is `None`, `~/.aiida` will be the default root config folder.
    """

    def __init__(self, config_folder: pathlib.Path | None = None) -> None:
        if config_folder is None:
            self._aiida_path = glb_aiida_config_folder
        else:
            self._aiida_path = config_folder

    @property
    def aiida_path(self) -> pathlib.Path:
        return self._aiida_path

    @property
    def daemon_dir(self) -> pathlib.Path:
        return self._aiida_path / DEFAULT_DAEMON_DIR_NAME

    @property
    def daemon_log_dir(self) -> pathlib.Path:
        return self._aiida_path / DEFAULT_DAEMON_DIR_NAME / DEFAULT_DAEMON_LOG_DIR_NAME

    @property
    def access_control_dir(self) -> pathlib.Path:
        return self._aiida_path / DEFAULT_ACCESS_CONTROL_DIR_NAME


def create_instance_directories(aiida_config_folder: pathlib.Path | None) -> None:
    """Create the base directories required for a new AiiDA instance.

    This will create the base AiiDA directory defined by the glb_aiida_config_folder variable, unless it already exists.
    Subsequently, it will create the daemon directory within it and the daemon log directory.
    """
    from aiida.common import ConfigurationError

    path_resolver = AiiDAConfigPathResolver(aiida_config_folder)

    list_of_paths = [
        path_resolver.aiida_path,
        path_resolver.daemon_dir,
        path_resolver.daemon_log_dir,
        path_resolver.access_control_dir,
    ]

    umask = os.umask(DEFAULT_UMASK)

    try:
        for path in list_of_paths:
            if path is path_resolver.aiida_path and not path.exists():
                warnings.warn(f'Creating AiiDA configuration folder `{path}`.')

            try:
                path.mkdir(parents=True, exist_ok=True)
            except OSError as exc:
                raise ConfigurationError(f'could not create the `{path}` configuration directory: {exc}') from exc
    finally:
        _ = os.umask(umask)


def get_configuration_directory():
    """Return the path of the configuration directory.

    The location of the configuration directory is defined following these heuristics in order:

        * If the ``AIIDA_PATH`` variable is set, all the paths will be checked to see if they contain a
          configuration folder. The first one to be encountered will be set as ``glb_aiida_config_folder``. If none of them
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
    global glb_aiida_config_folder
    glb_aiida_config_folder = aiida_config_folder or get_configuration_directory()

    create_instance_directories(glb_aiida_config_folder)


# Initialize the configuration directory settings
set_configuration_directory()
