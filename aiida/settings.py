# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################

import os


from aiida.backends import settings

from aiida.common.exceptions import ConfigurationError, MissingConfigurationError
from aiida.common.setup import (get_config, get_secret_key, get_property,
                                get_profile_config, get_default_profile,
                                parse_repository_uri)



USE_TZ = True

try:
    confs = get_config()
except MissingConfigurationError:
    raise MissingConfigurationError("Please run the AiiDA Installation, no config found")

if settings.AIIDADB_PROFILE is None:
    raise ConfigurationError("AIIDADB_PROFILE not defined, did you load django "
                             "through the AiiDA load_dbenv()?")

profile_conf = get_profile_config(settings.AIIDADB_PROFILE, conf_dict=confs)

# put all database specific portions of settings here
BACKEND = profile_conf.get('AIIDADB_BACKEND', 'django')
DBENGINE = profile_conf.get('AIIDADB_ENGINE', '')
DBNAME = profile_conf.get('AIIDADB_NAME', '')
DBUSER = profile_conf.get('AIIDADB_USER', '')
DBPASS = profile_conf.get('AIIDADB_PASS', '')
DBHOST = profile_conf.get('AIIDADB_HOST', '')
DBPORT = profile_conf.get('AIIDADB_PORT', '')
REPOSITORY_URI = profile_conf.get('AIIDADB_REPOSITORY_URI', '')


# Checks on the REPOSITORY_* variables
try:
    REPOSITORY_URI
except NameError:
    raise ConfigurationError(
        "Please setup correctly the REPOSITORY_URI variable to "
        "a suitable directory on which you have write permissions.")

# Note: this variable might disappear in the future
REPOSITORY_PROTOCOL, REPOSITORY_PATH = parse_repository_uri(REPOSITORY_URI)

if settings.IN_DOC_MODE:
    pass
elif REPOSITORY_PROTOCOL == 'file':
    if not os.path.isdir(REPOSITORY_PATH):
        try:
            # Try to create the local repository folders with needed parent
            # folders
            os.makedirs(REPOSITORY_PATH)
        except OSError:
            # Possibly here due to permission problems
            raise ConfigurationError(
                "Please setup correctly the REPOSITORY_PATH variable to "
                "a suitable directory on which you have write permissions. "
                "(I was not able to create the directory.)")
else:
    raise ConfigurationError("Only file protocol supported")


def get_repository_config(name=None):
    """
    Retrieve the 'name' repository from the configuration file. If 'name' is not specified, the default
    repository will be used. Returns the repository name and its configuration dictionary
    
    :param name: name of the repository configuration to retrieve, if not specified default is used
    :return: repository name and the repository configuration dictionary
    """
    try:
        repository_conf = profile_conf['repository']
        repository_avail = repository_conf['available']
        repository_default = repository_conf['default']
    except KeyError as exception:
        raise ConfigurationError("Invalid repository configuration")

    if name is None:
        repository_name = repository_default
    else:
        repository_name = name

    try:
        repository_config = repository_avail[repository_name]
    except KeyError as exception:
        raise ConfigurationError("The chosen repository '{}' is not defined in the configuration".format(repository_name))

    return repository_name, repository_config

def get_repository(name=None):
    """
    Retrieve a fully configured instance of Repository. The 'name' will determine the dictionary of parameters
    that will be taken from the configuration, which should contain the key 'type' which will determine the
    type of the Repository implementation that will be constructed

    :param name: name of the repository configuration to retrieve, if not specified default is used
    :return: Repository
    """
    from aiida.repository import construct_backend as construct_repository

    try:
        repository_name, repository_config = get_repository_config(name)
    except ConfigurationError as exception:
        raise

    try:
        repository_type = repository_config['type'];
    except KeyError as exception:
        raise ConfigurationError("The chosen repository '{}' does not specify a type in 'type'".format(repository_name))

    repository = construct_repository(repository_type, repository_config)

    return repository