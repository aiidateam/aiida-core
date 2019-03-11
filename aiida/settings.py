# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import
import os
from aiida.backends import settings
from aiida.common.exceptions import ConfigurationError, MissingConfigurationError
from aiida.common.setup import parse_repository_uri
from aiida.manage.configuration import get_config


TESTING_MODE = False

try:
    config = get_config()
except MissingConfigurationError:
    raise MissingConfigurationError("Please run the AiiDA installation, no config found")

if settings.AIIDADB_PROFILE is None:
    raise ConfigurationError("AIIDADB_PROFILE not defined, did you load django "
                             "through the AiiDA load_dbenv()?")

PROFILE = config.current_profile
PROFILE_CONF = PROFILE.dictionary

# put all database specific portions of settings here
BACKEND = PROFILE_CONF.get('AIIDADB_BACKEND', 'django')
DBENGINE = PROFILE_CONF.get('AIIDADB_ENGINE', '')
DBNAME = PROFILE_CONF.get('AIIDADB_NAME', '')
DBUSER = PROFILE_CONF.get('AIIDADB_USER', '')
DBPASS = PROFILE_CONF.get('AIIDADB_PASS', '')
DBHOST = PROFILE_CONF.get('AIIDADB_HOST', '')
DBPORT = PROFILE_CONF.get('AIIDADB_PORT', '')
REPOSITORY_URI = PROFILE_CONF.get('AIIDADB_REPOSITORY_URI', '')


# Checks on the REPOSITORY_* variables
try:
    REPOSITORY_URI
except NameError:
    raise ConfigurationError(
        "Please setup correctly the REPOSITORY_URI variable to "
        "a suitable directory on which you have write permissions.")

# Note: this variable might disappear in the future
REPOSITORY_PROTOCOL, REPOSITORY_PATH = parse_repository_uri(REPOSITORY_URI)

if settings.IN_RT_DOC_MODE:
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
