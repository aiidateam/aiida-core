# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################

from __future__ import absolute_import
from aiida.backends import settings
from aiida.common.exceptions import InvalidOperation
from aiida.common.setup import get_default_profile_name, get_profile_config


# Possible choices for backend
BACKEND_DJANGO = "django"
BACKEND_SQLA = "sqlalchemy"


def load_profile(profile=None):
    """
    Load the profile. This function is called by load_dbenv and SHOULD NOT
    be called by the user by hand.
    """
    if settings.LOAD_PROFILE_CALLED:
        raise InvalidOperation('You cannot call  multiple times!')

    settings.LOAD_PROFILE_CALLED = True

    if settings.AIIDADB_PROFILE is not None:
        if profile is not None and profile != settings.AIIDADB_PROFILE:
            raise ValueError('Error in profile loading')
    else:
        if profile is None:
            profile = get_default_profile_name()

        settings.AIIDADB_PROFILE = profile

    config = get_profile_config(settings.AIIDADB_PROFILE)

    # Check if AIIDADB_BACKEND is set and if not error (with message)
    # Migration script should put it in profile (config.json)
    settings.BACKEND = config.get('AIIDADB_BACKEND', BACKEND_DJANGO)


def is_profile_loaded():
    """
    Return True if the profile has already been loaded
    """
    return settings.LOAD_PROFILE_CALLED
