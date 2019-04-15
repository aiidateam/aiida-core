# -*- coding: utf-8 -*-

__copyright__ = u"Copyright (c), This file is part of the AiiDA platform. For further information please visit http://www.aiida.net/. All rights reserved."
__license__ = "MIT license, see LICENSE.txt file."
__authors__ = "The AiiDA team."
__version__ = "0.7.0.1"

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