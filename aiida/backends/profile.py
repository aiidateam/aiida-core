# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################

from aiida.backends import settings
from aiida.common.setup import (DEFAULT_PROCESS, get_default_profile,
                                get_profile_config)
from aiida.common.exceptions import InvalidOperation


# Possible choices for backend
BACKEND_DJANGO = "django"
BACKEND_SQLA = "sqlalchemy"


def load_profile(process=None, profile=None):
    """
    Load the profile. This function is called by load_dbenv and SHOULD NOT
    be called by the user by hand.
    """
    if settings.LOAD_PROFILE_CALLED:
        raise InvalidOperation("You cannot call load_profile multiple times!")
    settings.LOAD_PROFILE_CALLED = True

    # settings.CURRENT_AIIDADB_PROCESS should always be defined
    # by either verdi or the deamon
    if settings.CURRENT_AIIDADB_PROCESS is None and process is None:
        # This is for instance the case of a python script containing a
        # 'load_dbenv()' command and run with python

        settings.CURRENT_AIIDADB_PROCESS = DEFAULT_PROCESS
    elif (process is not None and
          process != settings.CURRENT_AIIDADB_PROCESS):
        ## The user specified a process that is different from the current one

        # I re-set the process
        settings.CURRENT_AIIDADB_PROCESS = process
        # I also remove the old profile
        settings.AIIDADB_PROFILE = None

    if settings.AIIDADB_PROFILE is not None:
        if profile is not None and profile != settings.AIIDADB_PROFILE:
            raise ValueError("Error in profile loading.")
    else:
        if profile is not None:
            the_profile = profile
        else:
            the_profile = get_default_profile(
                settings.CURRENT_AIIDADB_PROCESS)
        settings.AIIDADB_PROFILE = the_profile

    config = get_profile_config(settings.AIIDADB_PROFILE)

    # Check if AIIDADB_BACKEND is set and if not error (with message)
    # Migration script should put it in profile (config.json)
    settings.BACKEND = config.get("AIIDADB_BACKEND", BACKEND_DJANGO)


def is_profile_loaded():
    """
    Return True if the profile has already been loaded
    """
    return settings.LOAD_PROFILE_CALLED


