# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################


LOAD_DBENV_CALLED = False
LOAD_PROFILE_CALLED = False
CURRENT_AIIDADB_PROCESS = None
AIIDADB_PROFILE = None
AIIDANODES_UUID_VERSION = 4

BACKEND = None

TEST_REPOSITORY = None

# This is used (and should be set to true) for the correct compilation
# of the documentation on readthedocs
IN_DOC_MODE = False

# The following is a dummy config.json configuration that it is used for the
# proper compilation of the documentation on readthedocs.
DUMMY_CONF_FILE = (
    {"default_profiles": {"daemon": "default", "verdi": "default"},
     "profiles": {"default": {"AIIDADB_ENGINE": "postgresql_psycopg2",
                              "AIIDADB_PASS": "123", "AIIDADB_NAME": "aiidadb",
                              "AIIDADB_HOST": "localhost",
                              "AIIDADB_BACKEND": "django",
                              "AIIDADB_PORT": "5432",
                              "default_user_email": "aiida@epfl.ch",
                              "TIMEZONE": "Europe/Zurich",
                              "AIIDADB_REPOSITORY_URI":
                                  "file:///repository",
                              "AIIDADB_USER": "aiida"}}})