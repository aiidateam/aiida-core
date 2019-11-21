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

import errno
import os

USE_TZ = True

DEFAULT_UMASK = 0o0077
DEFAULT_AIIDA_PATH_VARIABLE = 'AIIDA_PATH'
DEFAULT_AIIDA_PATH = '~'
DEFAULT_AIIDA_USER = 'aiida@localhost'
DEFAULT_CONFIG_DIR_NAME = '.aiida'
DEFAULT_CONFIG_FILE_NAME = 'config.json'
DEFAULT_CONFIG_INDENT_SIZE = 4
DEFAULT_DAEMON_DIR_NAME = 'daemon'
DEFAULT_DAEMON_LOG_DIR_NAME = 'log'

AIIDA_CONFIG_FOLDER = None
DAEMON_DIR = None
DAEMON_LOG_DIR = None


def create_instance_directories():
    """Create the base directories required for a new AiiDA instance.

    This will create the base AiiDA directory defined by the AIIDA_CONFIG_FOLDER variable, unless it already exists.
    Subsequently, it will create the daemon directory within it and the daemon log directory.
    """
    directory_base = os.path.expanduser(AIIDA_CONFIG_FOLDER)
    directory_daemon = os.path.join(directory_base, DAEMON_DIR)
    directory_daemon_log = os.path.join(directory_base, DAEMON_LOG_DIR)

    umask = os.umask(DEFAULT_UMASK)

    try:
        create_directory(directory_base)
        create_directory(directory_daemon)
        create_directory(directory_daemon_log)
    finally:
        os.umask(umask)


def create_directory(path):
    """Attempt to create the configuration folder at the given path skipping if it already exists

    :param path: an absolute path to create a directory at
    """
    from aiida.common import ConfigurationError

    try:
        os.makedirs(path)
    except OSError as exception:
        if exception.errno != errno.EEXIST:
            raise ConfigurationError("could not create the '{}' configuration directory".format(path))


def set_configuration_directory():
    """Determine the location of the configuration directory and set the related global variables.

    The location of the configuration folder will be determined and optionally created following these heuristics:

        * If the `AIIDA_PATH` variable is set, all the paths will be checked to see if they contain a configuration
          folder. The first one to be encountered will be set as `AIIDA_CONFIG_FOLDER`. If none of them contain one,
          a configuration folder will be created in the last path considered.
        * If the `AIIDA_PATH` variable is not set the `DEFAULT_AIIDA_PATH` value will be used as base path and if it
          does not yet contain a configuration folder, one will be created.

    In principle then, a configuration folder should always be found or automatically created.
    """
    # pylint: disable = global-statement
    global AIIDA_CONFIG_FOLDER
    global DAEMON_DIR
    global DAEMON_LOG_DIR

    environment_variable = os.environ.get(DEFAULT_AIIDA_PATH_VARIABLE, None)

    if environment_variable:

        # Loop over all the paths in the `AIIDA_PATH` variable to see if any of them contain a configuration folder
        for base_dir_path in [os.path.expanduser(path) for path in environment_variable.split(':') if path]:

            AIIDA_CONFIG_FOLDER = os.path.expanduser(os.path.join(base_dir_path))

            # Only add the base config directory name to the base path if it does not already do so
            # Someone might already include it in the environment variable. e.g.: AIIDA_PATH=/home/some/path/.aiida
            if not AIIDA_CONFIG_FOLDER.endswith(DEFAULT_CONFIG_DIR_NAME):
                AIIDA_CONFIG_FOLDER = os.path.join(AIIDA_CONFIG_FOLDER, DEFAULT_CONFIG_DIR_NAME)

            # If the directory exists, we leave it set and break the loop
            if os.path.isdir(AIIDA_CONFIG_FOLDER):
                break

    else:
        # The `AIIDA_PATH` variable is not set, so default to the default path and try to create it if it does not exist
        AIIDA_CONFIG_FOLDER = os.path.expanduser(os.path.join(DEFAULT_AIIDA_PATH, DEFAULT_CONFIG_DIR_NAME))

    DAEMON_DIR = os.path.join(AIIDA_CONFIG_FOLDER, DEFAULT_DAEMON_DIR_NAME)
    DAEMON_LOG_DIR = os.path.join(DAEMON_DIR, DEFAULT_DAEMON_LOG_DIR_NAME)

    create_instance_directories()


# Initialize the configuration directory settings
set_configuration_directory()
