# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Base settings required for the configuration of an AiiDA instance."""
import os
import pathlib
import typing
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

AIIDA_CONFIG_FOLDER: typing.Optional[pathlib.Path] = None
DAEMON_DIR: typing.Optional[pathlib.Path] = None
DAEMON_LOG_DIR: typing.Optional[pathlib.Path] = None
ACCESS_CONTROL_DIR: typing.Optional[pathlib.Path] = None


def create_instance_directories():
    """Create the base directories required for a new AiiDA instance.

    This will create the base AiiDA directory defined by the AIIDA_CONFIG_FOLDER variable, unless it already exists.
    Subsequently, it will create the daemon directory within it and the daemon log directory.
    """
    from aiida.common import ConfigurationError

    directory_base = pathlib.Path(AIIDA_CONFIG_FOLDER).expanduser()
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


def set_configuration_directory(aiida_config_folder: pathlib.Path = None):
    """Determine location of configuration directory, set related global variables and create instance directories.

    The location of the configuration folder will be determined and optionally created following these heuristics:

        * If an explicit path is provided by `aiida_config_folder`, that will be set as the configuration folder.
        * Otherwise, if the `AIIDA_PATH` variable is set, all the paths will be checked to see if they contain a
          configuration folder. The first one to be encountered will be set as `AIIDA_CONFIG_FOLDER`. If none of them
          contain one, a configuration folder will be created in the last path considered.
        * If the `AIIDA_PATH` variable is not set the `DEFAULT_AIIDA_PATH` value will be used as base path and if it
          does not yet contain a configuration folder, one will be created.

    In principle then, a configuration folder should always be found or automatically created.
    """
    # pylint: disable = global-statement
    global AIIDA_CONFIG_FOLDER
    global DAEMON_DIR
    global DAEMON_LOG_DIR
    global ACCESS_CONTROL_DIR

    environment_variable = os.environ.get(DEFAULT_AIIDA_PATH_VARIABLE, None)

    if aiida_config_folder is not None:
        AIIDA_CONFIG_FOLDER = aiida_config_folder
    elif environment_variable:

        # Loop over all the paths in the `AIIDA_PATH` variable to see if any of them contain a configuration folder
        for base_dir_path in [path for path in environment_variable.split(':') if path]:

            AIIDA_CONFIG_FOLDER = pathlib.Path(base_dir_path).expanduser()

            # Only add the base config directory name to the base path if it does not already do so
            # Someone might already include it in the environment variable. e.g.: AIIDA_PATH=/home/some/path/.aiida
            if AIIDA_CONFIG_FOLDER.name != DEFAULT_CONFIG_DIR_NAME:
                AIIDA_CONFIG_FOLDER = AIIDA_CONFIG_FOLDER / DEFAULT_CONFIG_DIR_NAME

            # If the directory exists, we leave it set and break the loop
            if AIIDA_CONFIG_FOLDER.is_dir():
                break

    else:
        # The `AIIDA_PATH` variable is not set, so default to the default path and try to create it if it does not exist
        AIIDA_CONFIG_FOLDER = pathlib.Path(DEFAULT_AIIDA_PATH).expanduser() / DEFAULT_CONFIG_DIR_NAME

    DAEMON_DIR = AIIDA_CONFIG_FOLDER / DEFAULT_DAEMON_DIR_NAME
    DAEMON_LOG_DIR = DAEMON_DIR / DEFAULT_DAEMON_LOG_DIR_NAME
    ACCESS_CONTROL_DIR = AIIDA_CONFIG_FOLDER / DEFAULT_ACCESS_CONTROL_DIR_NAME

    create_instance_directories()


# Initialize the configuration directory settings
set_configuration_directory()
