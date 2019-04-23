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

    # Load the general load_dbenv.
    from aiida.backends.utils import load_dbenv
    load_dbenv(profile=profile_name)

    execute_from_command_line(actual_argv)
