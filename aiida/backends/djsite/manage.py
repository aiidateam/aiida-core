#!/usr/bin/env python
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
import sys


if __name__ == "__main__":
    from django.core.management import execute_from_command_line

    # Copy sys.argv
    actual_argv = sys.argv[:]

    # Check if there is also a cmdline option is --aiida-profile=PROFILENAME
    try:
        first_cmdline_option = sys.argv[1]
    except IndexError:
        first_cmdline_option = None

    profile_name = None  # Use the default profile if not specified
    if first_cmdline_option is not None:
        cmdprefix = "--aiida-profile="
        if first_cmdline_option.startswith(cmdprefix):
            profile_name = first_cmdline_option[len(cmdprefix):]
            # I remove the argument I just read
            actual_argv = [actual_argv[0]] + actual_argv[2:]

    if actual_argv[1] == 'migrate':
        # Perform the same loading procedure as the normal load_dbenv does
        from aiida.backends import settings
        settings.LOAD_DBENV_CALLED = True
        # We load the needed profile.
        # This is going to set global variables in settings, including
        # settings.BACKEND
        from aiida.backends.profile import load_profile, BACKEND_DJANGO
        load_profile(profile=profile_name)
        if settings.BACKEND != BACKEND_DJANGO:
            from aiida.common.exceptions import InvalidOperation
            raise InvalidOperation("A Django migration procedure is initiated "
                                   "but a different backend is used!")
        # We load the Django specific _load_dbenv_noschemacheck
        # When there will be a need for SQLAlchemy for a schema migration,
        # we may abstract thw _load_dbenv_noschemacheck and make a common
        # one for both backends
        from aiida.backends.djsite.utils import _load_dbenv_noschemacheck
        _load_dbenv_noschemacheck(profile=profile_name)
    else:
        # Load the general load_dbenv.
        from aiida.backends.utils import load_dbenv
        load_dbenv(profile=profile_name)

    execute_from_command_line(actual_argv)
