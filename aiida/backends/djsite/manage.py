#!/usr/bin/env python
# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

import click

from aiida.cmdline.params import options


@click.command()
@options.PROFILE(required=True)
@click.argument('command', nargs=-1)
def main(profile, command):
    """Simple wrapper around the Django command line tool that first loads an AiiDA profile."""
    from django.core.management import execute_from_command_line

    # Load the general load_dbenv.
    from aiida.manage.configuration import load_profile
    from aiida.manage.manager import get_manager

    load_profile(profile=profile.name)
    manager = get_manager()
    manager._load_backend(schema_check=False)

    # The `execute_from_command` expects a list of command line arguments where the first is the program name that one
    # would normally call directly. Since this is now replaced by our `click` command we just spoof a random name.
    argv = ['basename'] + list(command)
    execute_from_command_line(argv)


if __name__ == '__main__':
    main()
