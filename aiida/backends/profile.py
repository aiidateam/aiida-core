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

from aiida.backends import settings
from aiida.common.exceptions import InvalidOperation


# Possible choices for backend
BACKEND_DJANGO = 'django'
BACKEND_SQLA = 'sqlalchemy'


def load_profile(profile=None):
    """
    Load the profile. This function is called by load_dbenv and SHOULD NOT
    be called by the user by hand.
    """
    from aiida.common.log import configure_logging
    from aiida.manage.configuration import get_config

    if settings.LOAD_PROFILE_CALLED:
        raise InvalidOperation('You cannot call load_profile multiple times!')

    config = get_config()

    settings.LOAD_PROFILE_CALLED = True

    if settings.AIIDADB_PROFILE is not None:
        if profile is not None and profile != settings.AIIDADB_PROFILE:
            raise ValueError('Error in profile loading')
    else:
        if profile is None:
            profile = config.default_profile_name

        settings.AIIDADB_PROFILE = profile

    # Reconfigure the logging to make sure that profile specific logging configuration options are taken into account.
    # Also set `with_orm=True` to make sure that the `DBLogHandler` is configured as well.
    configure_logging(with_orm=True)

    profile = config.get_profile(profile)

    # Check if AIIDADB_BACKEND is set and if not error (with message)
    # Migration script should put it in profile (config.json)
    settings.BACKEND = profile.dictionary.get('AIIDADB_BACKEND', BACKEND_DJANGO)


def is_profile_loaded():
    """
    Return True if the profile has already been loaded
    """
    return settings.LOAD_PROFILE_CALLED
