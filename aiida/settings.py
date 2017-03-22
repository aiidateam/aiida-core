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

from aiida.common.exceptions import ConfigurationError
from aiida.common.setup import (get_config, get_secret_key, get_property,
                                get_profile_config, get_default_profile,
                                parse_repository_uri)



USE_TZ = True

try:
    confs = get_config()
except ConfigurationError:
    raise ConfigurationError("Please run the AiiDA Installation, no config found")

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


## Checks on the REPOSITORY_* variables
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
